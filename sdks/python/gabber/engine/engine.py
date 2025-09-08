"""
Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

SPDX-License-Identifier: Apache-2.0
"""

import asyncio
import json
from typing import Any, Callable, Dict, List, Optional, Protocol
from generated import runtime
from .publication import Publication
from . import types
from media import VirtualCamera, VirtualMicrophone

import logging  # For debug logging, replace console.debug with logging.debug

from livekit import rtc

# Assuming the following imports exist in the Python project:
# from pad.Pad import PropertyPad, SinkPad, SourcePad
# from LocalTrack import LocalAudioTrack, LocalVideoTrack, LocalTrack
# from Subscription import Subscription
# from Publication import Publication
# from generated.runtime import (
#     MCPServer, PadValue, Payload, RuntimeEvent, RuntimeRequest,
#     RuntimeRequestPayload_LockPublisher, RuntimeResponsePayload
# )


class EngineHandler(Protocol):
    """Optional handler for engine events."""

    def on_connection_state_change(self, state: types.ConnectionState) -> None:
        pass


class Engine:
    def __init__(self, params: Dict[str, Optional[EngineHandler]]):
        logging.debug("Creating new Engine instance")
        self._livekit_room: rtc.Room = rtc.Room()
        self.handler: Optional[EngineHandler] = params.get("handler")
        self._last_emitted_connection_state: types.ConnectionState = "disconnected"
        self._runtime_request_id_counter: int = 1
        self._pending_requests: Dict[str, Dict[str, Callable]] = {}
        self._pad_value_handlers: Dict[str, List[Callable[[Any], None]]] = {}
        self.setup_room_event_listeners()

    @property
    def connection_state(self) -> types.ConnectionState:
        if self._livekit_room.connection_state == rtc.ConnectionState.CONN_CONNECTED:
            # Assuming remote_participants is a dict-like with .values()
            agent_participants = [
                p
                for p in self._livekit_room.remote_participants.values()
                if p.identity.startswith("agent-")
            ]
            if len(agent_participants) > 0:
                return "connected"
            else:
                return "waiting_for_engine"

        if self._livekit_room.connection_state in (
            rtc.ConnectionState.CONN_RECONNECTING,
        ):
            return "connecting"
        return "disconnected"

    def _emit_connection_state_change(self) -> None:
        if self.handler is not None and hasattr(
            self.handler, "on_connection_state_change"
        ):
            if self._last_emitted_connection_state == self.connection_state:
                return  # No change, do not emit
            self._last_emitted_connection_state = self.connection_state
            self.handler.on_connection_state_change(self._last_emitted_connection_state)

    async def connect(self, *, connection_details: types.ConnectionDetails) -> None:
        await self._livekit_room.connect(
            connection_details.url, connection_details.token
        )

    async def disconnect(self) -> None:
        await self._livekit_room.disconnect()

    async def publish_to_node(
        self, *, publish_node: str, device: VirtualCamera | VirtualMicrophone
    ) -> "Publication":
        lock_payload = runtime.RuntimeRequestPayloadLockPublisher(
            type="lock_publisher", publish_node=publish_node
        )

        resp = await self.runtime_request(lock_payload)
        if resp.type != "lock_publisher":
            raise ValueError("Unexpected response type")

        if not resp.success:
            raise ValueError("Publisher node already locked")

        track_name = ""
        if isinstance(device, VirtualCamera):
            track_name = publish_node + ":video"
        elif isinstance(device, VirtualMicrophone):
            track_name = publish_node + ":audio"

        pub = Publication(
            node_id=publish_node,
            livekit_room=self._livekit_room,
            track_name=track_name,
            device=device,
        )
        pub._start()
        return pub

    async def list_mcp_servers(self) -> List[runtime.MCPServer]:
        payload = runtime.RuntimeRequestPayloadListMCPServers(type="list_mcp_servers")
        response = await self.runtime_request(payload)
        if response.type != "list_mcp_servers":
            raise ValueError("Unexpected response type")
        return response.servers

    async def subscribe_to_node(self, params: SubscribeParams) -> "Subscription":
        return Subscription(
            {
                "nodeId": params["outputOrPublishNodeId"],
                "livekitRoom": self._livekit_room,
            }
        )

    async def runtime_request(
        self, payload: types.RuntimeRequestPayload
    ) -> types.RuntimeResponsePayload:
        topic = "runtime_api"
        request_id = str(self._runtime_request_id_counter)
        self._runtime_request_id_counter += 1
        req = runtime.RuntimeRequest(req_id=request_id, payload=payload, type="request")
        loop = asyncio.get_running_loop()
        future: asyncio.Future[types.RuntimeResponsePayload] = loop.create_future()
        self._pending_requests[request_id] = {
            "res": lambda response: future.set_result(response),
            "rej": lambda error: future.set_exception(ValueError(error)),
        }
        data_bytes = json.dumps(req).encode("utf-8")
        await self._livekit_room.local_participant.publish_data(data_bytes, topic=topic)
        return await future

    def get_source_pad(self, node_id: str, pad_id: str) -> "SourcePad[PadValue]":
        return SourcePad(
            {
                "nodeId": node_id,
                "padId": pad_id,
                "livekitRoom": self._livekit_room,
                "engine": self,
            }
        )

    def get_sink_pad(self, node_id: str, pad_id: str) -> "SinkPad[PadValue]":
        return SinkPad(
            {
                "nodeId": node_id,
                "padId": pad_id,
                "livekitRoom": self._livekit_room,
                "engine": self,
            }
        )

    def get_property_pad(self, node_id: str, pad_id: str) -> "PropertyPad[PadValue]":
        return PropertyPad(
            {
                "nodeId": node_id,
                "padId": pad_id,
                "livekitRoom": self._livekit_room,
                "engine": self,
            }
        )

    def setup_room_event_listeners(self) -> None:
        def on_connected():
            self._emit_connection_state_change()

        self._livekit_room.on("connected", on_connected)

        def on_disconnected(reason: Any):
            self._emit_connection_state_change()

        self._livekit_room.on("disconnected", on_disconnected)

        def on_participant_connected(participant: rtc.RemoteParticipant):
            self._emit_connection_state_change()

        self._livekit_room.on("participant_connected", on_participant_connected)

        def on_participant_disconnected(participant: rtc.RemoteParticipant):
            self._emit_connection_state_change()

        self._livekit_room.on("participant_disconnected", on_participant_disconnected)

        self._livekit_room.on("data_received", self._on_data)

    def _add_pad_value_handler(
        self, node_id: str, pad_id: str, handler: Callable[[types.PadValue], None]
    ) -> None:
        key = f"{node_id}:{pad_id}"
        if key not in self._pad_value_handlers:
            self._pad_value_handlers[key] = []
        self._pad_value_handlers[key].append(handler)

    def _remove_pad_value_handler(
        self, node_id: str, pad_id: str, handler: Callable[[types.PadValue], None]
    ) -> None:
        key = f"{node_id}:{pad_id}"
        if key in self._pad_value_handlers:
            self._pad_value_handlers[key] = [
                h for h in self._pad_value_handlers[key] if h != handler
            ]

    def _on_data(
        self,
        data: bytes,
        participant: Optional[rtc.RemoteParticipant],
        kind: rtc.DataPacketKind,
        topic: Optional[str],
    ) -> None:
        msg_str = data.decode("utf-8")
        test_msg = json.loads(msg_str)
        logging.debug("Received data on topic: %s, %s", topic, test_msg)
        if topic != "runtime_api":
            return  # Ignore data not on this pad's channel
        msg = json.loads(msg_str)
        if msg["type"] == "ack":
            logging.debug("Received ACK for request: %s", msg["req_id"])
        elif msg["type"] == "complete":
            logging.debug("Received COMPLETE for request: %s", msg["req_id"])
            if "error" in msg:
                logging.error("Error in request: %s", msg["error"])
                pending_request = self._pending_requests.get(msg["req_id"])
                if pending_request:
                    pending_request["rej"](msg["error"])
            else:
                pending_request = self._pending_requests.get(msg["req_id"])
                if pending_request:
                    pending_request["res"](msg["payload"])
            self._pending_requests.pop(msg["req_id"], None)
        elif msg["type"] == "event":
            # Assuming RuntimeEvent(msg)
            casted_msg: runtime.RuntimeEvent = msg  # Type cast
            payload_event = casted_msg.payload
            if payload_event.type == "value":
                node_id = payload_event.node_id
                pad_id = payload_event.pad_id
                key = f"{node_id}:{pad_id}"
                handlers = self._pad_value_handlers.get(key, [])
                for handler in handlers:
                    handler(payload_event.value)
