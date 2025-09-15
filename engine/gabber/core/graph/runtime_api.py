# Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
# SPDX-License-Identifier: SUL-1.0

import asyncio
from typing import Annotated, Any, Literal
from pydantic import BaseModel, Field
from livekit import rtc
from dataclasses import dataclass
from .. import node, pad, runtime_types, mcp
import logging
from ..editor import serialize
from ..node import Node
from nodes.core.media.publish import Publish

PING_BYTES = "ping".encode("utf-8")


class RuntimeApi:
    def __init__(
        self,
        *,
        room: rtc.Room,
        nodes: list[node.Node],
    ):
        self.room = room
        self.nodes = nodes
        self._publish_locks: dict[str, PublishLock] = {}

    def _trigger_value_from_pad_value(self, value: Any):
        v = serialize.serialize_pad_value(value)
        ev_value: PadValue
        if isinstance(v, bool):
            ev_value = PadValue_Boolean(value=v)
        elif isinstance(v, int):
            ev_value = PadValue_Integer(value=v)
        elif isinstance(v, float):
            ev_value = PadValue_Float(value=v)
        elif isinstance(v, str):
            ev_value = PadValue_String(value=v)
        elif isinstance(value, runtime_types.AudioClip):
            trans = value.transcription if value.transcription else ""
            ev_value = PadValue_AudioClip(transcript=trans, duration=value.duration)
        elif isinstance(value, runtime_types.VideoClip):
            ev_value = PadValue_VideoClip(duration=value.duration)
        else:
            ev_value = PadValue_Trigger()

        return ev_value

    async def run(self):
        node_pad_lookup: dict[tuple[str, str], pad.Pad] = {
            (n.id, p.get_id()): p for n in self.nodes for p in n.pads
        }
        all_pads = list(node_pad_lookup.values())

        @dataclass(frozen=True)
        class QueueItem:
            payload: BaseModel
            participant: rtc.RemoteParticipant | None

        dc_queue = asyncio.Queue[QueueItem | None]()

        def on_pad(p: pad.Pad, value: Any):
            ev_value = self._trigger_value_from_pad_value(value)
            dc_queue.put_nowait(
                QueueItem(
                    payload=RuntimeEvent(
                        payload=RuntimeEventPayload_Value(
                            value=ev_value,
                            node_id=p.get_owner_node().id,
                            pad_id=p.get_id(),
                        )
                    ),
                    participant=None,
                )
            )

        for p in all_pads:
            p._add_update_handler(on_pad)

        def on_data(packet: rtc.DataPacket):
            if not packet.topic or packet.topic != "runtime_api":
                return

            try:
                request = RuntimeRequest.model_validate_json(packet.data)
            except Exception as e:
                logging.error(f"Invalid runtime_api request: {e}", exc_info=e)
                return
            req_id = request.req_id
            ack_resp = RuntimeRequestAck(req_id=req_id, type="ack")
            complete_resp = RuntimeResponse(req_id=req_id, type="complete")

            dc_queue.put_nowait(
                QueueItem(payload=ack_resp, participant=packet.participant)
            )

            if request.payload.type == "lock_publisher":
                payload = request.payload
                existing_lock = self._publish_locks.get(payload.publish_node)
                if not packet.participant:
                    complete_resp.error = "Participant is required."
                    dc_queue.put_nowait(
                        QueueItem(payload=complete_resp, participant=packet.participant)
                    )
                    return

                if existing_lock and not existing_lock.is_locked():
                    self._publish_locks.pop(payload.publish_node)

                if existing_lock and existing_lock.is_locked():
                    if existing_lock.participant_id != packet.participant.identity:
                        complete_resp.payload = RuntimeResponsePayload_LockPublisher(
                            success=False
                        )
                        dc_queue.put_nowait(
                            QueueItem(
                                payload=complete_resp, participant=packet.participant
                            )
                        )
                        return

                pub_node = [n for n in self.nodes if n.id == payload.publish_node]
                if len(pub_node) != 1 or not isinstance(pub_node[0], Publish):
                    complete_resp.error = "Publish node not found."
                    dc_queue.put_nowait(
                        QueueItem(payload=complete_resp, participant=packet.participant)
                    )
                    return

                self._publish_locks[payload.publish_node] = PublishLock(
                    self.room,
                    packet.participant.identity,
                    payload.publish_node,
                    pub_node[0],
                )

                complete_resp.payload = RuntimeResponsePayload_LockPublisher(
                    type="lock_publisher", success=True
                )
                dc_queue.put_nowait(
                    QueueItem(payload=complete_resp, participant=packet.participant)
                )
            elif request.payload.type == "push_value":
                payload = request.payload
                node_id = payload.node_id
                pad_id = payload.pad_id
                pad_obj = node_pad_lookup.get((node_id, pad_id))
                if not pad_obj:
                    logging.error(f"Pad {pad_id} in node {node_id} not found.")
                    complete_resp.error = f"Pad {pad_id} in node {node_id} not found."
                    dc_queue.put_nowait(
                        QueueItem(payload=complete_resp, participant=packet.participant)
                    )
                    return
                if not isinstance(pad_obj, pad.SourcePad):
                    logging.error(f"Pad {pad_id} in node {node_id} is not a SourcePad.")
                    complete_resp.error = (
                        f"Pad {pad_id} in node {node_id} is not a SourcePad."
                    )
                    dc_queue.put_nowait(
                        QueueItem(payload=complete_resp, participant=packet.participant)
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
                        QueueItem(payload=complete_resp, participant=packet.participant)
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
                        QueueItem(payload=complete_resp, participant=packet.participant)
                    )
                )
                ctx.complete()
            elif request.payload.type == "get_value":
                payload = request.payload
                node_id = payload.node_id
                pad_id = payload.pad_id
                pad_obj = node_pad_lookup.get((node_id, pad_id))
                if not isinstance(pad_obj, pad.PropertyPad):
                    logging.error(
                        f"Pad {pad_id} in node {node_id} is not a PropertyPad."
                    )
                    complete_resp.error = (
                        f"Pad {pad_id} in node {node_id} is not a PropertyPad."
                    )
                    dc_queue.put_nowait(
                        QueueItem(payload=complete_resp, participant=packet.participant)
                    )
                    return

                value = pad_obj.get_value()
                value_obj = self._trigger_value_from_pad_value(value)

                # Don't get node references
                if isinstance(value, Node):
                    return

                complete_resp.payload = RuntimeResponsePayload_GetValue(
                    type="get_value", value=value_obj
                )
                dc_queue.put_nowait(
                    QueueItem(payload=complete_resp, participant=packet.participant)
                )
            else:
                logging.error(f"Unknown request type: {request.payload.type}")
                complete_resp.error = f"Unknown request type: {request.payload.type}"
                dc_queue.put_nowait(
                    QueueItem(payload=complete_resp, participant=packet.participant)
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
                        topic="runtime_api",
                    )
                except Exception as e:
                    logging.error(f"Error sending data packet: {e}", exc_info=e)

        await dc_queue_consumer()
        self.room.off("data_received", on_data)


class PadValue_String(BaseModel):
    type: Literal["string"] = "string"
    value: str


class PadValue_Boolean(BaseModel):
    type: Literal["boolean"] = "boolean"
    value: bool


class PadValue_Integer(BaseModel):
    type: Literal["integer"] = "integer"
    value: int


class PadValue_Float(BaseModel):
    type: Literal["float"] = "float"
    value: float


class PadValue_Trigger(BaseModel):
    type: Literal["trigger"] = "trigger"


class PadValue_AudioClip(BaseModel):
    type: Literal["audio_clip"] = "audio_clip"
    transcript: str
    duration: float


class PadValue_VideoClip(BaseModel):
    type: Literal["video_clip"] = "video_clip"
    duration: float


PadValue = Annotated[
    PadValue_String
    | PadValue_Integer
    | PadValue_Float
    | PadValue_Boolean
    | PadValue_Trigger
    | PadValue_AudioClip
    | PadValue_VideoClip,
    Field(discriminator="type", description="Type of the pad triggered value"),
]


class RuntimeEventPayload_Value(BaseModel):
    type: Literal["value"] = "value"
    value: PadValue
    node_id: str
    pad_id: str


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
    node_id: str
    pad_id: str


class RuntimeRequestPayload_GetValue(BaseModel):
    type: Literal["get_value"] = "get_value"
    node_id: str
    pad_id: str


class RuntimeRequestPayload_LockPublisher(BaseModel):
    type: Literal["lock_publisher"] = "lock_publisher"
    publish_node: str


RuntimeRequestPayload = Annotated[
    RuntimeRequestPayload_PushValue
    | RuntimeRequestPayload_GetValue
    | RuntimeRequestPayload_LockPublisher,
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
    value: PadValue


class RuntimeResponsePayload_LockPublisher(BaseModel):
    type: Literal["lock_publisher"] = "lock_publisher"
    success: bool


RuntimeResponsePayload = Annotated[
    RuntimeResponsePayload_PushValue
    | RuntimeResponsePayload_GetValue
    | RuntimeResponsePayload_LockPublisher,
    Field(discriminator="type", description="Payload for the runtime request complete"),
]


class RuntimeResponse(BaseModel):
    type: Literal["complete"] = "complete"
    req_id: str
    error: str | None = None
    payload: RuntimeResponsePayload | None = None


class PublishLock:
    def __init__(
        self, room: rtc.Room, participant_id: str, publish_node: str, node: Publish
    ):
        self.participant_id = participant_id
        self._publish_node = publish_node
        self._room = room
        self._node = node
        self._unlock_tasks: list[asyncio.Task] = []
        self._done = False
        self._node.set_allowed_participant(participant_id)
        self._loop_t = asyncio.create_task(self._lock_loop())

    async def _lock_loop(self):
        # Give participant 10 seconds to publish their track
        await asyncio.sleep(10.0)
        while True:
            is_publishing = False
            for rp in self._room.remote_participants.values():
                for t in rp.track_publications.values():
                    if self._check_relevant(t, rp):
                        is_publishing = True

            if is_publishing:
                await asyncio.sleep(2.0)
                continue

            break

        self._node.unset_allowed_participant(self.participant_id)
        self._done = True

    def _check_relevant(
        self, pub: rtc.RemoteTrackPublication, part: rtc.RemoteParticipant
    ) -> bool:
        if self._done:
            return False

        name_split = pub.name.split(":")
        if len(name_split) <= 1:
            logging.warning(f"Published track with invalid name: {pub.name}")
            return False

        if name_split[0] != self._publish_node:
            return False

        if part.identity != self.participant_id:
            return False

        return True

    def is_locked(self) -> bool:
        return not self._done


# For easier generation
class DummyType(BaseModel):
    req: RuntimeRequest
    runtime_request_payload: RuntimeRequestPayload
    resp: RuntimeResponse
    runtime_response_payload: RuntimeResponsePayload
    ev: RuntimeEvent
    runtime_event_payload: RuntimeEventPayload
    pad_value: PadValue
