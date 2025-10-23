# Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
# SPDX-License-Identifier: SUL-1.0

import asyncio
from typing import Annotated, Any, Literal
from pydantic import BaseModel, Field, TypeAdapter
from livekit import rtc
from dataclasses import dataclass
from .. import node, pad
import logging
from ..node import Node
from gabber.nodes.core.media.publish import Publish
from ..types import client, mapper, pad_constraints

client_value_adapter = TypeAdapter(client.ClientPadValue)

PING_BYTES = "ping".encode("utf-8")


@dataclass(frozen=True)
class QueueItem:
    payload: BaseModel
    participant: rtc.RemoteParticipant | None


class RuntimeApi:
    def __init__(
        self,
        *,
        room: rtc.Room,
    ):
        self.room = room
        self._publish_locks: dict[str, PublishLock] = {}
        self._dc_queue = asyncio.Queue[QueueItem | None]()

    def emit_logs(self, items: list["RuntimeEventPayload_LogItem"]):
        self._dc_queue.put_nowait(
            QueueItem(
                payload=RuntimeEvent(
                    payload=RuntimeEventPayload_Logs(type="logs", items=items)
                ),
                participant=None,
            )
        )

    async def run(self, nodes: list[node.Node]):
        node_pad_lookup: dict[tuple[str, str], pad.Pad] = {
            (n.id, p.get_id()): p for n in nodes for p in n.pads
        }
        all_pads = list(node_pad_lookup.values())

        def on_pad(p: pad.Pad, value: Any):
            ev_value = mapper.Mapper.runtime_to_client(value)
            self._dc_queue.put_nowait(
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

            self._dc_queue.put_nowait(
                QueueItem(payload=ack_resp, participant=packet.participant)
            )

            if request.payload.type == "lock_publisher":
                payload = request.payload
                existing_lock = self._publish_locks.get(payload.publish_node)
                if not packet.participant:
                    complete_resp.error = "Participant is required."
                    self._dc_queue.put_nowait(
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
                        self._dc_queue.put_nowait(
                            QueueItem(
                                payload=complete_resp, participant=packet.participant
                            )
                        )
                        return

                pub_node = [n for n in nodes if n.id == payload.publish_node]
                if len(pub_node) != 1 or not isinstance(pub_node[0], Publish):
                    complete_resp.error = "Publish node not found."
                    self._dc_queue.put_nowait(
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
                self._dc_queue.put_nowait(
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
                    self._dc_queue.put_nowait(
                        QueueItem(payload=complete_resp, participant=packet.participant)
                    )
                    return
                if not isinstance(pad_obj, pad.SourcePad):
                    logging.error(f"Pad {pad_id} in node {node_id} is not a SourcePad.")
                    complete_resp.error = (
                        f"Pad {pad_id} in node {node_id} is not a SourcePad."
                    )
                    self._dc_queue.put_nowait(
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
                    self._dc_queue.put_nowait(
                        QueueItem(payload=complete_resp, participant=packet.participant)
                    )
                    return
                parsed: client.ClientPadValue = None
                if payload.value is not None:
                    parsed = client_value_adapter.validate_python(payload.value)
                value = mapper.Mapper.client_to_runtime(parsed)
                ctx = pad.RequestContext(parent=None, publisher_metadata=None)
                complete_resp.payload = RuntimeResponsePayload_PushValue(
                    type="push_value"
                )
                pad_obj.push_item(value, ctx)
                ctx.add_done_callback(
                    lambda _: self._dc_queue.put_nowait(
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
                    self._dc_queue.put_nowait(
                        QueueItem(payload=complete_resp, participant=packet.participant)
                    )
                    return

                value = mapper.Mapper.runtime_to_client(pad_obj.get_value())

                # Don't get node references
                if isinstance(value, Node):
                    return

                complete_resp.payload = RuntimeResponsePayload_GetValue(
                    type="get_value", value=value
                )
                self._dc_queue.put_nowait(
                    QueueItem(payload=complete_resp, participant=packet.participant)
                )
            elif request.payload.type == "get_list_items":
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
                    self._dc_queue.put_nowait(
                        QueueItem(payload=complete_resp, participant=packet.participant)
                    )
                    return

                value = pad_obj.get_value()
                if not isinstance(value, list):
                    logging.error(f"Pad {pad_id} in node {node_id} is not a list.")
                    complete_resp.error = (
                        f"Pad {pad_id} in node {node_id} is not a list."
                    )
                    self._dc_queue.put_nowait(
                        QueueItem(payload=complete_resp, participant=packet.participant)
                    )
                    return

                # TODO
                ev_values = []
                complete_resp.payload = RuntimeResponsePayload_GetListItems(
                    type="get_list_items", items=ev_values
                )
                self._dc_queue.put_nowait(
                    QueueItem(payload=complete_resp, participant=packet.participant)
                )
            else:
                logging.error(f"Unknown request type: {request.payload.type}")
                complete_resp.error = f"Unknown request type: {request.payload.type}"
                self._dc_queue.put_nowait(
                    QueueItem(payload=complete_resp, participant=packet.participant)
                )

        self.room.on("data_received", on_data)

        async def dc_queue_consumer():
            while True:
                item = await self._dc_queue.get()
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


class RuntimeEventPayload_Value(BaseModel):
    type: Literal["value"] = "value"
    value: client.ClientPadValue
    node_id: str
    pad_id: str


class RuntimeEventPayload_LogItem(BaseModel):
    message: str
    level: str
    timestamp: str
    node: str | None = None
    subgraph: str | None = None
    pad: str | None = None


class RuntimeEventPayload_Logs(BaseModel):
    type: Literal["logs"] = "logs"
    items: list[RuntimeEventPayload_LogItem]


RuntimeEventPayload = Annotated[
    RuntimeEventPayload_Value | RuntimeEventPayload_Logs,
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


class RuntimeRequestPayload_GetListItems(BaseModel):
    type: Literal["get_list_items"] = "get_list_items"
    node_id: str
    pad_id: str


class RuntimeRequestPayload_LockPublisher(BaseModel):
    type: Literal["lock_publisher"] = "lock_publisher"
    publish_node: str


RuntimeRequestPayload = Annotated[
    RuntimeRequestPayload_PushValue
    | RuntimeRequestPayload_GetValue
    | RuntimeRequestPayload_GetListItems
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
    value: client.ClientPadValue


class RuntimeResponsePayload_GetListItems(BaseModel):
    type: Literal["get_list_items"] = "get_list_items"
    items: list[client.ClientPadValue]


class RuntimeResponsePayload_LockPublisher(BaseModel):
    type: Literal["lock_publisher"] = "lock_publisher"
    success: bool


RuntimeResponsePayload = Annotated[
    RuntimeResponsePayload_PushValue
    | RuntimeResponsePayload_GetValue
    | RuntimeResponsePayload_GetListItems
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
    pad_value: client.ClientPadValue
    pad_constraint: pad_constraints.PadConstraint
    log_item: RuntimeEventPayload_LogItem
