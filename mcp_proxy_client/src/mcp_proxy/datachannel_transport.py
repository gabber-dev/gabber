# Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
# SPDX-License-Identifier: SUL-1.0

import json
import logging

import mcp.types as types
from anyio.streams.memory import MemoryObjectReceiveStream, MemoryObjectSendStream
from livekit import rtc
from mcp.shared.message import SessionMessage

logger = logging.getLogger(__name__)


async def datachannel_client_proxy(
    room: rtc.Room,
    mcp_name: str,
    other_read_stream: MemoryObjectReceiveStream[SessionMessage | Exception],
    other_write_stream: MemoryObjectSendStream[SessionMessage],
) -> rtc.Room:
    topic = f"__mcp__:{mcp_name}"

    def on_message(packet: rtc.DataPacket):
        if packet.topic != topic:
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
                    json.dumps(msg_dict), topic=topic
                )

    room.on("data_received", on_message)
    await read_loop()
    room.off("data_received", on_message)
    return room
