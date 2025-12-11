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
from gabber.nodes.core.tool.tool_group import ToolGroup
from ..types import client, mapper, pad_constraints, runtime

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
        self._tc_acks: dict[str, asyncio.Future[None]] = {}
        self._tc_results: dict[
            str, asyncio.Future[ToolCallResponse_Payload_Result]
        ] = {}

    def emit_logs(self, items: list["RuntimeEventPayload_LogItem"]):
        self._dc_queue.put_nowait(
            QueueItem(
                payload=RuntimeEvent(
                    payload=RuntimeEventPayload_Logs(type="logs", items=items)
                ),
                participant=None,
            )
        )

    async def client_tool_call_task(self, nodes: list[node.Node]):
        tool_group_nodes = [n for n in nodes if isinstance(n, ToolGroup)]
        all_tasks = set()

        async def single_tg_task(
            node: ToolGroup,
            td: runtime.ToolDefinition,
            tc: runtime.ToolCall,
            fut: asyncio.Future[str],
        ):
            assert isinstance(td.destination, runtime.ToolDefinitionDestination_Client)
            client_td = mapper.Mapper.runtime_to_client(td)
            assert isinstance(client_td, client.ToolDefinition)
            client_tc = client.ToolCall(
                call_id=tc.call_id, index=tc.index, name=tc.name, arguments=tc.arguments
            )
            assert isinstance(client_tc, client.ToolCall)

            ack_fut = asyncio.Future[None]()
            self._tc_acks[client_tc.call_id] = ack_fut
            res_fut = asyncio.Future[ToolCallResponse_Payload_Result]()
            self._tc_results[client_tc.call_id] = res_fut
            req = ToolCallRequest(
                payload=ToolCallRequest_Payload_InitiateRequest(
                    tool_definition=client_td,
                    tool_call=client_tc,
                )
            )
            await self.room.local_participant.publish_data(
                req.model_dump_json().encode("utf-8"),
                destination_identities=[],
                topic="tool_call",
            )

            try:
                await asyncio.wait_for(ack_fut, timeout=5.0)
                node.logger.info(
                    f"Tool call '{client_tc.call_id}' initiated with client."
                )
                del self._tc_acks[client_tc.call_id]
            except asyncio.TimeoutError:
                fut.set_exception(
                    Exception("Timeout initiating tool call with client.")
                )
                return

            try:
                result_resp = await asyncio.wait_for(res_fut, timeout=60.0)
                node.logger.info(
                    f"Tool call '{client_tc.call_id}' completed from client."
                )
                del self._tc_results[client_tc.call_id]
                if result_resp.error:
                    fut.set_exception(Exception(result_resp.error))
                else:
                    fut.set_result(result_resp.result or "")
            except asyncio.TimeoutError:
                fut.set_exception(Exception("Timeout waiting for tool call result."))

        async def tg_task(tg: ToolGroup):
            q = tg.client_call_queue
            while True:
                (td, tc, fut) = await q.get()
                t = asyncio.create_task(single_tg_task(tg, td, tc, fut))
                all_tasks.add(t)
                t.add_done_callback(lambda _: all_tasks.remove(t))

        tc_tasks = [asyncio.create_task(tg_task(tg)) for tg in tool_group_nodes]
        await asyncio.gather(*tc_tasks)

    async def run(self, nodes: list[node.Node]):
        tool_task = asyncio.create_task(self.client_tool_call_task(nodes))
        node_pad_lookup: dict[tuple[str, str], pad.Pad] = {
            (n.id, p.get_id()): p for n in nodes for p in n.pads
        }
        all_pads = list(node_pad_lookup.values())

        def on_pad(p: pad.Pad, value: Any):
            try:
                ev_value = mapper.Mapper.runtime_to_client(value)
            except Exception as e:
                logging.error(
                    f"Error mapping pad value to client value: {e}", exc_info=e
                )
                return
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
            if not packet.topic:
                return

            if packet.topic == "runtime_api":
                on_runtime_api_data(packet)
            elif packet.topic == "tool_call":
                on_tool_call_data(packet)

        def on_tool_call_data(packet: rtc.DataPacket):
            try:
                response = ToolCallResponse.model_validate_json(packet.data)
                if response.payload.type == "initiate_ack":
                    payload = response.payload
                    ack_fut = self._tc_acks.get(payload.call_id)
                    if ack_fut and not ack_fut.done():
                        ack_fut.set_result(None)

                elif response.payload.type == "result":
                    payload = response.payload
                    res_fut = self._tc_results.get(payload.call_id)
                    if res_fut and not res_fut.done():
                        res_fut.set_result(payload)
            except Exception as e:
                logging.error(f"Invalid tool_call response: {e}", exc_info=e)
                return

        def on_runtime_api_data(packet: rtc.DataPacket):
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
                parsed: client.ClientPadValue = None
                if payload.value is not None:
                    parsed = client_value_adapter.validate_python(payload.value)
                value = mapper.Mapper.client_to_runtime(parsed)
                if isinstance(pad_obj, pad.SourcePad):
                    ctx = pad.RequestContext(parent=None, publisher_metadata=None)
                    pad_obj.push_item(value, ctx)
                    complete_resp.payload = RuntimeResponsePayload_PushValue(
                        type="push_value"
                    )
                    ctx.add_done_callback(
                        lambda _: self._dc_queue.put_nowait(
                            QueueItem(
                                payload=complete_resp, participant=packet.participant
                            )
                        )
                    )
                    ctx.complete()
                elif isinstance(pad_obj, pad.SinkPad):
                    if not isinstance(pad_obj, pad.PropertyPad):
                        logging.error(
                            f"Pad {pad_id} in node {node_id} is not a PropertyPad."
                        )
                        complete_resp.error = (
                            f"Pad {pad_id} in node {node_id} is not a PropertyPad."
                        )
                        self._dc_queue.put_nowait(
                            QueueItem(
                                payload=complete_resp, participant=packet.participant
                            )
                        )
                        return
                    ctx = pad.RequestContext(parent=None, publisher_metadata=None)
                    pad_obj._set_value(value)
                    complete_resp.payload = RuntimeResponsePayload_PushValue(
                        type="push_value"
                    )
                    ctx.add_done_callback(
                        lambda _: self._dc_queue.put_nowait(
                            QueueItem(
                                payload=complete_resp, participant=packet.participant
                            )
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
        await tool_task
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


class ToolCallRequest_Payload_InitiateRequest(BaseModel):
    type: Literal["initiate_request"] = "initiate_request"
    tool_definition: client.ToolDefinition
    tool_call: client.ToolCall


ToolCallRequestPayload = Annotated[
    ToolCallRequest_Payload_InitiateRequest,
    Field(discriminator="type", description="Request for a tool call"),
]


class ToolCallRequest(BaseModel):
    type: Literal["tool_call_request"] = "tool_call_request"
    payload: ToolCallRequestPayload


class ToolCallResponse_Payload_InitiateAck(BaseModel):
    type: Literal["initiate_ack"] = "initiate_ack"
    call_id: str


class ToolCallResponse_Payload_Result(BaseModel):
    type: Literal["result"] = "result"
    call_id: str
    result: str | None
    error: str | None


ToolCallResponsePayload = Annotated[
    ToolCallResponse_Payload_InitiateAck | ToolCallResponse_Payload_Result,
    Field(discriminator="type", description="Response for a tool call"),
]


class ToolCallResponse(BaseModel):
    type: Literal["tool_call_response"] = "tool_call_response"
    payload: ToolCallResponsePayload


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
    tool_call_request: ToolCallRequest
    tool_call_response: ToolCallResponse
