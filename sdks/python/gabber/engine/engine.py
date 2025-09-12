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
import logging
from typing import Any, Callable, Dict, List, Optional

from livekit import rtc

from ..generated import runtime
from ..media import VirtualCamera, VirtualMicrophone
from . import types
from .pad import PropertyPad, SinkPad, SourcePad
from .publication import Publication
from .subscription import Subscription

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class Engine:
    def __init__(
        self,
        *,
        on_connection_state_change: Optional[
            Callable[[types.ConnectionState], None]
        ] = None,
    ):
        self._livekit_room = rtc.Room()
        self.setup_room_event_listeners()
        self._on_connection_state_change = on_connection_state_change
        self._last_emitted_connection_state: types.ConnectionState = "disconnected"
        self._runtime_request_id_counter: int = 1
        self._pending_futs: Dict[str, Dict[str, Callable]] = {}
        self._pad_value_handlers: Dict[str, List[Callable[[Any], None]]] = {}

    @property
    def connection_state(self) -> types.ConnectionState:
        if self._livekit_room.connection_state == rtc.ConnectionState.CONN_CONNECTED:
            # Assuming remote_participants is a dict-like with .values()
            agent_participants = [
                p
                for p in self._livekit_room.remote_participants.values()
                if p.identity == "gabber-engine"
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
        if self._on_connection_state_change is not None:
            if self._last_emitted_connection_state == self.connection_state:
                return  # No change, do not emit
            self._last_emitted_connection_state = self.connection_state
            self._on_connection_state_change(self._last_emitted_connection_state)

    async def connect(self, *, connection_details: types.ConnectionDetails) -> None:
        await self._livekit_room.connect(
            connection_details.url, connection_details.token
        )

        while True:
            if self.connection_state == "connected":
                break
            await asyncio.sleep(0.2)

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
        await pub.start()
        return pub

    async def subscribe_to_node(self, *, output_or_publish_node: str):
        sub = Subscription(
            node_id=output_or_publish_node, livekit_room=self._livekit_room
        )
        await sub.start()
        return sub

    async def list_mcp_servers(self) -> List[runtime.MCPServer]:
        payload = runtime.RuntimeRequestPayloadListMCPServers(type="list_mcp_servers")
        retries = 3
        last_exception = None
        for attempt in range(retries):
            try:
                response = await self.runtime_request(payload)
                if response.type == "list_mcp_servers":
                    return response.servers
            except Exception as e:
                last_exception = e

        if last_exception:
            raise last_exception
        raise ValueError("Unexpected response type")

    async def runtime_request(
        self, payload: types.RuntimeRequestPayload, timeout: float = 2.0
    ) -> types.RuntimeResponsePayload:
        topic = "runtime_api"
        request_id = str(self._runtime_request_id_counter)
        self._runtime_request_id_counter += 1
        req = runtime.RuntimeRequest(req_id=request_id, payload=payload, type="request")
        future = asyncio.Future[types.RuntimeResponsePayload]()
        self._pending_futs[request_id] = future
        try:
            await self._livekit_room.local_participant.publish_data(
                req.model_dump_json(),
                topic=topic,
                destination_identities=["gabber-engine"],
            )
            return await asyncio.wait_for(future, timeout=timeout)
        except Exception as e:
            future.set_exception(e)
            raise

    def get_source_pad(self, node_id: str, pad_id: str) -> "SourcePad":
        return SourcePad(
            node_id=node_id, pad_id=pad_id, engine=self, livekit_room=self._livekit_room
        )

    def get_sink_pad(self, node_id: str, pad_id: str) -> "SinkPad":
        return SinkPad(
            node_id=node_id, pad_id=pad_id, engine=self, livekit_room=self._livekit_room
        )

    def get_property_pad(self, node_id: str, pad_id: str) -> "PropertyPad":
        return PropertyPad(
            node_id=node_id, pad_id=pad_id, engine=self, livekit_room=self._livekit_room
        )

    def setup_room_event_listeners(self) -> None:
        def on_connected(state: rtc.ConnectionState):
            self._emit_connection_state_change()

        def on_participant_connected(participant: rtc.RemoteParticipant):
            self._emit_connection_state_change()

        def on_participant_disconnected(participant: rtc.RemoteParticipant):
            self._emit_connection_state_change()

        self._livekit_room.on("connection_state_changed", on_connected)
        self._livekit_room.on("participant_connected", on_participant_connected)
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
        packet: rtc.DataPacket,
    ) -> None:
        if packet.participant and packet.participant.identity != "gabber-engine":
            return

        data = packet.data

        if packet.topic != "runtime_api":
            return  # Ignore data not on this pad's channel

        msg_str = data.decode("utf-8")
        msg = json.loads(msg_str)

        if msg["type"] == "ack":
            pass
        elif msg["type"] == "complete":
            resp = runtime.RuntimeResponse.model_validate(msg)
            payload = resp.payload
            if resp.error is not None:
                logging.error("Error in request: %s", msg["error"])
                pending_request = self._pending_futs.get(msg["req_id"])
                if pending_request:
                    pending_request.set_exception(Exception(msg["error"]))
            else:
                pending_request = self._pending_futs.get(msg["req_id"])
                if pending_request:
                    pending_request.set_result(payload)
            self._pending_futs.pop(msg["req_id"], None)
        elif msg["type"] == "event":
            resp = runtime.RuntimeEvent.model_validate(msg)
            payload = resp.payload
            if payload.type == "value":
                node_id = payload.node_id
                pad_id = payload.pad_id
                key = f"{node_id}:{pad_id}"
                handlers = self._pad_value_handlers.get(key, [])
                for handler in handlers:
                    handler(payload.value)
