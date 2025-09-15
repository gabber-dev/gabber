# Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
# SPDX-License-Identifier: SUL-1.0

import asyncio
import os
import logging
import re
import time
from typing import (
    Any,
    cast,
)

import json_repair
from gabber.core.runtime_types import (
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


class EmojiRemover:
    def __init__(self):
        # Regex pattern for common emoji Unicode ranges (covers most, but not all variants)
        self.emoji_pattern = re.compile(
            "["
            "\U0001f600-\U0001f64f"  # Emoticons
            "\U0001f300-\U0001f5ff"  # Symbols & pictographs
            "\U0001f680-\U0001f6ff"  # Transport & map symbols
            "\U0001f1e0-\U0001f1ff"  # Flags (iOS)
            "\U00002702-\U000027b0"  # Dingbats
            "\U000024c2-\U0001f251"  # Enclosed characters
            "\U0001f900-\U0001f9ff"  # Supplemental symbols & pictographs
            "\U00002600-\U000026ff"  # Miscellaneous symbols
            "\U00002b50-\U00002b55"  # Stars
            "\U00002300-\U000023ff"  # Miscellaneous technical
            "\U00002500-\U00002bef"  # Box drawing & more
            "\U00002000-\U0000206f"  # General punctuation (includes zero-width joiners for emoji sequences)
            "]+",
            flags=re.UNICODE,
        )

    def push_text(self, text: str) -> str:
        # Substitute matched emojis with an empty string
        return self.emoji_pattern.sub("", text)


# TODO: validate lock in runtime_api
async def audio_stream_provider(room: rtc.Room, track_name: str, participant: str):
    while True:
        await asyncio.sleep(0.2)
        for p in room.remote_participants.values():
            if p.kind == rtc.ParticipantKind.PARTICIPANT_KIND_AGENT:
                continue
            if p.identity != participant:
                continue
            for track_pub in p.track_publications.values():
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


# TODO: validate lock in runtime_api
async def video_stream_provider(room: rtc.Room, track_name: str, participant: str):
    while True:
        await asyncio.sleep(0.2)
        for p in room.remote_participants.values():
            if p.kind == rtc.ParticipantKind.PARTICIPANT_KIND_AGENT:
                continue
            if p.identity != participant:
                continue
            for track_pub in p.track_publications.values():
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
    thinking = False
    for delta in deltas:
        cnt = delta.content
        if not cnt:
            continue
        if thinking:
            split = cnt.split("</think>")
            if len(split) == 2:
                normal_cnt = split[1]
                content += normal_cnt
                thinking = False
        else:
            split = cnt.split("<think>")
            if len(split) == 2:
                normal_cnt = split[0]
                content += normal_cnt
                thinking = True
            else:
                content += cnt

    return content.strip()


def short_uuid():
    import uuid

    return str(uuid.uuid4())[:8]


__all__ = ["audio_stream_provider", "noop_task"]
