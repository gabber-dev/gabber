# Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
# SPDX-License-Identifier: SUL-1.0

import json
import asyncio
import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import anyio
import mcp.types as types
from anyio.streams.memory import MemoryObjectReceiveStream, MemoryObjectSendStream
from livekit import rtc
from mcp.shared.message import SessionMessage
from pydantic import ValidationError

logger = logging.getLogger(__name__)


async def datachannel_client_proxy(
    room: rtc.Room,
    other_read_stream: MemoryObjectReceiveStream[SessionMessage | Exception],
    other_write_stream: MemoryObjectSendStream[SessionMessage],
) -> rtc.Room:
    read_stream: MemoryObjectReceiveStream[SessionMessage | Exception]
    read_stream_writer: MemoryObjectSendStream[SessionMessage | Exception]
    write_stream: MemoryObjectSendStream[SessionMessage]
    write_stream_reader: MemoryObjectReceiveStream[SessionMessage]

    read_stream_writer, read_stream = anyio.create_memory_object_stream(0)
    write_stream, write_stream_reader = anyio.create_memory_object_stream(0)

    def on_message(packet: rtc.DataPacket):
        if packet.topic != "__mcp__":
            return
        logger.debug(f"Received data packet: {packet.data}")
        json_msg = types.JSONRPCMessage.model_validate_json(packet.data)
        sm = SessionMessage(json_msg)
        other_write_stream.send_nowait(sm)

    async def read_loop():
        async with other_read_stream:
            async for session_message in other_read_stream:
                if isinstance(session_message, Exception):
                    logger.error(f"Error in received message: {session_message}")
                    continue
                msg_dict = session_message.message.model_dump(
                    by_alias=True, mode="json", exclude_none=True
                )
                await room.local_participant.publish_data(
                    json.dumps(msg_dict), topic="__mcp__"
                )

    room.on("data_received", on_message)
    await read_loop()
    room.off("data_received", on_message)
    return room
