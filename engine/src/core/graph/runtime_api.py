# Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
# SPDX-License-Identifier: SUL-1.0

import asyncio
from typing import Annotated, Any, Literal
from pydantic import BaseModel, Field
from livekit import rtc
from dataclasses import dataclass
from core import node, pad, runtime_types
import logging
from core.editor import serialize


class RuntimeApi:
    def __init__(self, *, room: rtc.Room, nodes: list[node.Node]):
        self.room = room
        self.nodes = nodes

    async def run(self):
        node_pad_lookup: dict[tuple[str, str], pad.Pad] = {
            (n.id, p.get_id()): p for n in self.nodes for p in n.pads
        }
        all_pads = list(node_pad_lookup.values())

        @dataclass(frozen=True)
        class QueueItem:
            payload: BaseModel
            participant: rtc.RemoteParticipant | None
            node_id: str | None
            pad_id: str | None

        dc_queue = asyncio.Queue[QueueItem | None]()

        def on_pad(p: pad.Pad, value: Any):
            # Keep both raw value (for dataclasses) and serialized value (for primitives/BaseModels)
            v = serialize.serialize_pad_value(value)
            ev_value: PadTriggeredValue | None = None
            # Primitive types are serialized directly
            if isinstance(v, int):
                ev_value = PadTriggeredValue_Integer(value=v)
            elif isinstance(v, float):
                ev_value = PadTriggeredValue_Float(value=v)
            elif isinstance(v, str):
                ev_value = PadTriggeredValue_String(value=v)
            elif isinstance(v, bool):
                ev_value = PadTriggeredValue_Boolean(value=v)
            # Dataclasses from runtime_types are not BaseModels, so check against the raw value
            elif isinstance(value, runtime_types.AudioFrame):
                # Single frame: surface as audio_clip with the frame duration so UIs can pulse
                ev_value = PadTriggeredValue_AudioClip(
                    transcript="",
                    duration=value.original_data.duration,
                )
            elif isinstance(value, runtime_types.AudioClip):
                trans = value.transcription if value.transcription else ""
                ev_value = PadTriggeredValue_AudioClip(
                    transcript=trans, duration=value.duration
                )
            elif isinstance(value, runtime_types.VideoClip):
                ev_value = PadTriggeredValue_VideoClip(duration=value.duration)
            else:
                ev_value = PadTriggeredValue_Trigger()
            dc_queue.put_nowait(
                QueueItem(
                    payload=RuntimeEvent(
                        payload=RuntimeEventPayload_Value(
                            value=ev_value,
                        )
                    ),
                    participant=None,
                    node_id=p.get_owner_node().id,
                    pad_id=p.get_id(),
                )
            )

        for p in all_pads:
            p._add_update_handler(on_pad)

        def on_data(packet: rtc.DataPacket):
            if not packet.topic or not packet.topic.startswith("runtime:"):
                return

            split_topic = packet.topic.split(":")
            if len(split_topic) < 3:
                logging.error(f"Invalid topic format: {packet.topic}")
                return

            node_id = split_topic[1]
            pad_id = split_topic[2]
            request = RuntimeRequest.model_validate_json(packet.data)
            req_id = request.req_id
            ack_resp = RuntimeRequestAck(req_id=req_id)
            dc_queue.put_nowait(
                QueueItem(
                    payload=ack_resp,
                    participant=packet.participant,
                    node_id=node_id,
                    pad_id=pad_id,
                )
            )
            complete_resp = RuntimeResponse(req_id=req_id)
            if request.payload.type == "push_value":
                payload = request.payload
                pad_obj = node_pad_lookup.get((node_id, pad_id))
                if not pad_obj:
                    logging.error(f"Pad {pad_id} in node {node_id} not found.")
                    complete_resp.error = f"Pad {pad_id} in node {node_id} not found."
                    dc_queue.put_nowait(
                        QueueItem(
                            payload=complete_resp,
                            participant=packet.participant,
                            node_id=node_id,
                            pad_id=pad_id,
                        )
                    )
                    return
                if not isinstance(pad_obj, pad.SourcePad):
                    logging.error(f"Pad {pad_id} in node {node_id} is not a SourcePad.")
                    complete_resp.error = (
                        f"Pad {pad_id} in node {node_id} is not a SourcePad."
                    )
                    dc_queue.put_nowait(
                        QueueItem(
                            payload=complete_resp,
                            participant=packet.participant,
                            node_id=node_id,
                            pad_id=pad_id,
                        )
                    )
                    return

                tcs = pad_obj.get_type_constraints()
                if not tcs or len(tcs) != 1:
                    logging.error(
                        f"Pad {pad_id} in node {node_id} has no type constraints."
                    )
                    complete_resp.error = (
                        f"Pad {pad_id} in node {node_id} has no type constraints."
                    )
                    dc_queue.put_nowait(
                        QueueItem(
                            payload=complete_resp,
                            participant=packet.participant,
                            node_id=node_id,
                            pad_id=pad_id,
                        )
                    )
                    return

                value = serialize.deserialize_pad_value(tcs[0], payload.value)
                ctx = pad.RequestContext(parent=None)
                complete_resp.payload = RuntimeResponsePayload_PushValue(
                    type="push_value"
                )
                pad_obj.push_item(value, ctx)
                ctx.add_done_callback(
                    lambda _: dc_queue.put_nowait(
                        QueueItem(
                            payload=complete_resp,
                            participant=packet.participant,
                            node_id=node_id,
                            pad_id=pad_id,
                        )
                    )
                )
                ctx.complete()
            elif request.payload.type == "get_value":
                payload = request.payload
                pad_obj = node_pad_lookup.get((node_id, pad_id))
                if not isinstance(pad_obj, pad.PropertyPad):
                    logging.error(
                        f"Pad {pad_id} in node {node_id} is not a PropertyPad."
                    )
                    complete_resp.error = (
                        f"Pad {pad_id} in node {node_id} is not a PropertyPad."
                    )
                    dc_queue.put_nowait(
                        QueueItem(
                            payload=complete_resp,
                            participant=packet.participant,
                            node_id=node_id,
                            pad_id=pad_id,
                        )
                    )
                    return

                value = pad_obj.get_value()
                complete_resp.payload = RuntimeResponsePayload_GetValue(
                    type="get_value", value=value
                )
                dc_queue.put_nowait(
                    QueueItem(
                        payload=complete_resp,
                        participant=packet.participant,
                        node_id=node_id,
                        pad_id=pad_id,
                    )
                )
            else:
                logging.error(f"Unknown request type: {request.payload.type}")
                complete_resp.error = f"Unknown request type: {request.payload.type}"
                dc_queue.put_nowait(
                    QueueItem(
                        payload=complete_resp,
                        participant=packet.participant,
                        node_id=node_id,
                        pad_id=pad_id,
                    )
                )

        self.room.on("data_received", on_data)

        async def dc_queue_consumer():
            while True:
                item = await dc_queue.get()
                if item is None:
                    break

                try:
                    destination_identities: list[str] = []
                    payload_bytes = item.payload.model_dump_json().encode("utf-8")
                    if item.participant:
                        destination_identities.append(item.participant.identity)

                    await self.room.local_participant.publish_data(
                        payload_bytes,
                        destination_identities=destination_identities,
                        topic=f"runtime:{item.node_id}:{item.pad_id}",
                    )
                except Exception as e:
                    logging.error(f"Error sending data packet: {e}", exc_info=e)

        await dc_queue_consumer()
        self.room.off("data_received", on_data)


class PadTriggeredValue_String(BaseModel):
    type: Literal["string"] = "string"
    value: str


class PadTriggeredValue_Boolean(BaseModel):
    type: Literal["boolean"] = "boolean"
    value: bool


class PadTriggeredValue_Integer(BaseModel):
    type: Literal["integer"] = "integer"
    value: int


class PadTriggeredValue_Float(BaseModel):
    type: Literal["float"] = "float"
    value: float


class PadTriggeredValue_Trigger(BaseModel):
    type: Literal["trigger"] = "trigger"


class PadTriggeredValue_AudioClip(BaseModel):
    type: Literal["audio_clip"] = "audio_clip"
    transcript: str
    duration: float


class PadTriggeredValue_VideoClip(BaseModel):
    type: Literal["video_clip"] = "video_clip"
    duration: float


PadTriggeredValue = Annotated[
    PadTriggeredValue_String
    | PadTriggeredValue_Integer
    | PadTriggeredValue_Float
    | PadTriggeredValue_Boolean
    | PadTriggeredValue_Trigger
    | PadTriggeredValue_AudioClip
    | PadTriggeredValue_VideoClip,
    Field(discriminator="type", description="Type of the pad triggered value"),
]


class RuntimeEventPayload_Value(BaseModel):
    type: Literal["value"] = "value"
    value: PadTriggeredValue


RuntimeEventPayload = Annotated[
    RuntimeEventPayload_Value,
    Field(discriminator="type", description="Payload for the runtime event"),
]


class RuntimeEvent(BaseModel):
    type: Literal["event"] = "event"
    payload: RuntimeEventPayload


class RuntimeRequestPayload_PushValue(BaseModel):
    type: Literal["push_value"] = "push_value"
    value: Any = None


class RuntimeRequestPayload_GetValue(BaseModel):
    type: Literal["get_value"] = "get_value"


RuntimeRequestPayload = Annotated[
    RuntimeRequestPayload_PushValue | RuntimeRequestPayload_GetValue,
    Field(discriminator="type", description="Request to push data to a pad"),
]


class RuntimeRequest(BaseModel):
    type: Literal["request"] = "request"
    req_id: str
    payload: RuntimeRequestPayload


class RuntimeRequestAck(BaseModel):
    type: Literal["ack"] = "ack"
    req_id: str


class RuntimeResponsePayload_PushValue(BaseModel):
    type: Literal["push_value"] = "push_value"


class RuntimeResponsePayload_GetValue(BaseModel):
    type: Literal["get_value"] = "get_value"
    value: Any | None = None


RuntimeResponsePayload = Annotated[
    RuntimeResponsePayload_PushValue | RuntimeResponsePayload_GetValue,
    Field(discriminator="type", description="Payload for the runtime request complete"),
]


class RuntimeResponse(BaseModel):
    type: Literal["complete"] = "complete"
    req_id: str
    error: str | None = None
    payload: RuntimeResponsePayload | None = None
