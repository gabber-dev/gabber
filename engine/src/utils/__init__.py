# Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
# SPDX-License-Identifier: SUL-1.0

import asyncio
import logging
import time
from typing import (
    Any,
    TypeVar,
    cast,
)

import json_repair
from core.runtime_types import (
    ContextMessageContent_ChoiceDelta,
    ContextMessageContent_ToolCallDelta,
    ToolCall,
)
from livekit import rtc


async def noop_task():
    pass


class Timer:
    def __init__(self):
        self.start_time = time.time()
        self.end_time = None

    def stop(self):
        self.end_time = time.time()

    def get_time(self):
        if self.end_time:
            return self.end_time - self.start_time
        return time.time() - self.start_time

    def reset(self):
        self.start_time = time.time()

    def __str__(self):
        return str(self.get_time())

    def __repr__(self):
        return str(self.get_time())


def clear_queue(queue: asyncio.Queue):
    while True:
        try:
            queue.get_nowait()
        except asyncio.QueueEmpty:
            break


class ItalicRemover:
    def __init__(self):
        self.in_italic = False

    def push_text(self, text: str) -> str:
        res = ""
        for c in text:
            if self.in_italic:
                if c == "*":
                    self.in_italic = False
                continue
            else:
                if c == "*":
                    self.in_italic = True
                    continue
            res += c
        return res


class ParenthesisRemover:
    def __init__(self):
        self.in_p = False

    def push_text(self, text: str) -> str:
        res = ""
        for c in text:
            if self.in_p:
                if c == ")":
                    self.in_p = False
                continue
            else:
                if c == "(":
                    self.in_p = True
                    continue
            res += c
        return res


async def audio_stream_provider(room: rtc.Room, track_name: str):
    while True:
        await asyncio.sleep(0.2)
        for participant in room.remote_participants.values():
            if participant.kind == rtc.ParticipantKind.PARTICIPANT_KIND_AGENT:
                continue
            for track_pub in participant.track_publications.values():
                # This track is not yet subscribed, when it is subscribed it will
                # call the on_track_subscribed callback
                if track_pub.track is None:
                    continue

                if track_pub.kind != rtc.TrackKind.KIND_AUDIO:
                    continue

                if track_pub.name != track_name:
                    continue

                noise_canc = None

                # This track is not a audio track
                stream = rtc.AudioStream.from_track(
                    track=track_pub.track, noise_cancellation=noise_canc
                )
                logging.info(
                    f"got audio stream {track_pub.track.sid} {stream._sample_rate}"
                )
                return stream


async def video_stream_provider(room: rtc.Room, track_name: str):
    while True:
        await asyncio.sleep(0.2)
        for participant in room.remote_participants.values():
            if participant.kind == rtc.ParticipantKind.PARTICIPANT_KIND_AGENT:
                continue
            for track_pub in participant.track_publications.values():
                if track_pub.track is None:
                    continue

                if track_pub.kind != rtc.TrackKind.KIND_VIDEO:
                    continue

                if track_pub.name != track_name:
                    continue

                stream = rtc.VideoStream.from_track(track=track_pub.track)
                logging.info(f"got video stream {track_pub.track.sid}")
                return stream


def get_tool_calls_from_deltas(
    deltas: list[ContextMessageContent_ToolCallDelta],
) -> list[ToolCall]:
    arg_accumulate: dict[int, str] = {}
    id_lookup: dict[int, str] = {}
    name_lookup: dict[int, str] = {}
    max_index = -1
    for delta in deltas:
        if delta.index > max_index:
            max_index = delta.index
        if delta.index not in arg_accumulate:
            arg_accumulate[delta.index] = ""
        if delta.arguments:
            arg_accumulate[delta.index] += delta.arguments
        if delta.id:
            id_lookup[delta.index] = delta.id
        if delta.name:
            name_lookup[delta.index] = delta.name

    res: list[ToolCall] = []
    for i in range(max_index + 1):
        dict_args: dict[str, Any] = cast(Any, json_repair.loads(arg_accumulate[i]))
        if not isinstance(dict_args, dict):
            dict_args = {}

        name = name_lookup.get(i, "")
        index = i
        call_id = id_lookup.get(i, "")
        res.append(
            ToolCall(
                name=name,
                arguments=dict_args,
                call_id=call_id,
                index=index,
            )
        )

    return res


def get_tool_calls_from_choice_deltas(
    deltas: list[ContextMessageContent_ChoiceDelta],
) -> list[ToolCall]:
    all_tc_deltas: list[ContextMessageContent_ToolCallDelta] = []
    for delta in deltas:
        if delta.tool_calls:
            all_tc_deltas.extend(delta.tool_calls)

    return get_tool_calls_from_deltas(all_tc_deltas)


def get_full_content_from_deltas(
    deltas: list[ContextMessageContent_ChoiceDelta],
) -> str:
    content = ""
    for delta in deltas:
        if delta.content:
            content += delta.content
    return content


def short_uuid():
    import uuid

    return str(uuid.uuid4())[:8]


T = TypeVar("T")


__all__ = ["audio_stream_provider", "noop_task"]
