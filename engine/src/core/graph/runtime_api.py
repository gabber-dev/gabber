import asyncio
from typing import Annotated, Any, Literal
from pydantic import BaseModel, Field
from livekit import rtc
from dataclasses import dataclass
from core import node, pad
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

        @dataclass(frozen=True)
        class QueueItem:
            payload: BaseModel
            participant: rtc.RemoteParticipant | None
            node_id: str | None
            pad_id: str | None

        def on_data(packet: rtc.DataPacket):
            if not packet.topic or not packet.topic.startswith("runtime:"):
                return

            request = RuntimeRequest.model_validate_json(packet.data)
            req_id = request.req_id
            ack_resp = RuntimeRequestAck(req_id=req_id)
            dc_queue.put_nowait(
                QueueItem(
                    payload=ack_resp,
                    participant=packet.participant,
                    node_id=None,
                    pad_id=None,
                )
            )
            complete_resp = RuntimeResponse(req_id=req_id)
            if request.payload.type == "push_value":
                payload = request.payload
                pad_obj = node_pad_lookup.get((payload.node_id, payload.source_pad_id))
                if not isinstance(pad_obj, pad.SourcePad):
                    logging.error(
                        f"Pad {payload.source_pad_id} in node {payload.node_id} is not a SourcePad."
                    )
                    complete_resp.error = f"Pad {payload.source_pad_id} in node {payload.node_id} is not a SourcePad."
                    dc_queue.put_nowait(
                        QueueItem(
                            payload=complete_resp,
                            participant=packet.participant,
                            node_id=None,
                            pad_id=None,
                        )
                    )
                    return

                if not pad_obj:
                    logging.error(
                        f"Pad {payload.source_pad_id} in node {payload.node_id} not found."
                    )
                    complete_resp.error = f"Pad {payload.source_pad_id} in node {payload.node_id} not found."
                    dc_queue.put_nowait(
                        QueueItem(
                            payload=complete_resp,
                            participant=packet.participant,
                            node_id=None,
                            pad_id=None,
                        )
                    )
                    return

                value = serialize.deserialize_pad_value(
                    self.nodes, pad_obj, payload.value
                )
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
                            node_id=payload.node_id,
                            pad_id=payload.source_pad_id,
                        )
                    )
                )
                ctx.complete()
            elif request.payload.type == "get_value":
                payload = request.payload
                pad_obj = node_pad_lookup.get(
                    (payload.node_id, payload.property_pad_id)
                )
                if not isinstance(pad_obj, pad.PropertyPad):
                    logging.error(
                        f"Pad {payload.property_pad_id} in node {payload.node_id} is not a PropertyPad."
                    )
                    complete_resp.error = f"Pad {payload.property_pad_id} in node {payload.node_id} is not a PropertyPad."
                    dc_queue.put_nowait(
                        QueueItem(
                            payload=complete_resp,
                            participant=packet.participant,
                            node_id=payload.node_id,
                            pad_id=payload.property_pad_id,
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
                        node_id=payload.node_id,
                        pad_id=payload.property_pad_id,
                    )
                )
            else:
                logging.error(f"Unknown request type: {request.payload.type}")
                complete_resp.error = f"Unknown request type: {request.payload.type}"
                dc_queue.put_nowait(
                    QueueItem(
                        payload=complete_resp,
                        participant=packet.participant,
                        node_id=None,
                        pad_id=None,
                    )
                )

        self.room.on("data_received", on_data)
        dc_queue = asyncio.Queue[QueueItem | None]()
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

                    logging.info(
                        f"Sending data packet to {destination_identities} for node {item.node_id}, pad {item.pad_id}"
                    )
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


class PadTriggeredValue_Number(BaseModel):
    type: Literal["number"] = "number"
    value: float


class PadTriggeredValue_Trigger(BaseModel):
    type: Literal["trigger"] = "trigger"


class PadTriggeredValue_AudioClip(BaseModel):
    type: Literal["audio_clip"] = "audio_clip"
    transcript: str
    duration: float


class PadTriggeredValue_VideoClip(BaseModel):
    type: Literal["video_clip"] = "video_clip"
    transcript: str
    duration: float


PadTriggeredValue = Annotated[
    PadTriggeredValue_String
    | PadTriggeredValue_Boolean
    | PadTriggeredValue_Number
    | PadTriggeredValue_Trigger
    | PadTriggeredValue_AudioClip,
    Field(discriminator="type", description="Type of the pad triggered value"),
]


class RuntimeEvent_PadTriggered(BaseModel):
    type: Literal["pad_triggered"] = "pad_triggered"
    node_id: str
    pad_id: str
    value: PadTriggeredValue


RuntimeEvent = Annotated[
    RuntimeEvent_PadTriggered,
    Field(discriminator="type", description="Request to perform on the graph editor"),
]


class RuntimeRequestPayload_PushValue(BaseModel):
    type: Literal["push_value"] = "push_value"
    node_id: str
    source_pad_id: str
    value: Any = None


class RuntimeRequestPayload_GetValue(BaseModel):
    type: Literal["get_value"] = "get_value"
    node_id: str
    property_pad_id: str


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