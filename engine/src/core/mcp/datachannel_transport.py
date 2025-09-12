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


@asynccontextmanager
async def datachannel_host(
    room: rtc.Room, participant: str, mcp_name: str
) -> AsyncGenerator[
    tuple[
        MemoryObjectReceiveStream[SessionMessage | Exception],
        MemoryObjectSendStream[SessionMessage],
    ],
    None,
]:
    topic = f"__mcp__:{mcp_name}"
    read_stream: MemoryObjectReceiveStream[SessionMessage | Exception]
    read_stream_writer: MemoryObjectSendStream[SessionMessage | Exception]
    write_stream: MemoryObjectSendStream[SessionMessage]
    write_stream_reader: MemoryObjectReceiveStream[SessionMessage]

    read_stream_writer, read_stream = anyio.create_memory_object_stream(0)
    write_stream, write_stream_reader = anyio.create_memory_object_stream(0)

    packet_q = asyncio.Queue[rtc.DataPacket | None]()

    def on_message(packet: rtc.DataPacket):
        if packet.topic != topic:
            return

        if not packet.participant:
            return

        if packet.participant.identity != participant:
            return

        packet_q.put_nowait(packet)

    async def on_message_loop():
        while True:
            packet = await packet_q.get()
            if packet is None:
                break

            try:
                message = types.JSONRPCMessage.model_validate_json(packet.data)
                session_message = SessionMessage(message)
                await read_stream_writer.send(session_message)
            except ValidationError as exc:
                logging.error(f"DC message validation error: {exc}")
                # If JSON parse or model validation fails, send the exception
                await read_stream_writer.send(exc)
            except Exception as exc:
                logging.error(f"DC unexpected error: {exc}")
                await read_stream_writer.send(exc)

    async def dc_writer():
        """
        Reads JSON-RPC messages from write_stream_reader and
        sends them to the server.
        """
        async with write_stream_reader:
            async for session_message in write_stream_reader:
                # Convert to a dict, then to JSON
                msg_dict = session_message.message.model_dump(
                    by_alias=True, mode="json", exclude_none=True
                )
                await room.local_participant.publish_data(
                    json.dumps(msg_dict), topic=topic
                )

    room.on("data_received", on_message)
    async with anyio.create_task_group() as tg:
        # Start reader and writer tasks
        tg.start_soon(on_message_loop)
        tg.start_soon(dc_writer)

        # Yield the receive/send streams
        yield (read_stream, write_stream)

        # Once the caller's 'async with' block exits, we shut down
        tg.cancel_scope.cancel()

    room.off("data_received", on_message)
