# Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
# SPDX-License-Identifier: SUL-1.0

import asyncio
import logging
from typing import Any, cast

import aiohttp
import msgpack
from gabber.core.runtime_types import AudioClip, AudioFrame
from utils import short_uuid

from ..stt import (
    STT,
    STTEvent,
    STTEvent_EndOfTurn,
    STTEvent_SpeechStarted,
    STTEvent_Transcription,
)
from .exponential_moving_average import ExponentialMovingAverage

STEPS_PER_SECOND = 12.5
FLUSH_ZEROS_SECONDS = 1
COOLDOWN_SECONDS = 0.5
DRIFT_THRESHOLD = 3
PRE_BUFFER_SECONDS = 5.0

FLUSH_FRAME = AudioFrame.silence(FLUSH_ZEROS_SECONDS)


class Kyutai(STT):
    def __init__(self, *, port: int):
        self._port = port
        self._process_queue = asyncio.Queue[AudioFrame | None]()
        self._closed = False
        self._output_queue = asyncio.Queue[STTEvent | None]()

    def push_audio(self, audio: AudioFrame) -> None:
        self._process_queue.put_nowait(audio)

    async def run(self) -> None:
        while not self._closed:
            try:
                await self._run_ws()
            except Exception as e:
                logging.error("WebSocket connection error: %s", exc_info=e)

            await asyncio.sleep(1)

    async def _run_ws(self) -> None:
        audio_window = AudioWindow()
        audio_samples: int = 0

        async def rec_task(ws: aiohttp.ClientWebSocketResponse) -> None:
            nonlocal audio_samples
            while not self._closed:
                needs_flush = False

                if ws.closed:
                    break
                msg = await ws.receive()
                if msg.type == aiohttp.WSMsgType.CLOSED:
                    logging.info("WebSocket closed")
                    break
                elif msg.type == aiohttp.WSMsgType.ERROR:
                    logging.error("WebSocket error: %s", msg.data)
                    break
                elif msg.type == aiohttp.WSMsgType.BINARY:
                    data = cast(dict[str, Any], msgpack.unpackb(msg.data, raw=False))
                    if data["type"] == "Step":
                        buffered_pcm = data["buffered_pcm"]
                        if buffered_pcm > 24000:
                            logging.warning(
                                f"buffered pcm becoming large: {buffered_pcm}"
                            )
                        prs: list[float] = data["prs"]
                        needs_flush = audio_window.push_step(end_prob=prs[2])
                    elif data["type"] == "Word":
                        audio_window.push_word(
                            word=data["text"], start_time=data["start_time"]
                        )
                        audio_time = audio_samples / 24000.0
                        word_start = data["start_time"]
                        if abs(audio_time - word_start) > DRIFT_THRESHOLD:
                            logging.warning(
                                "Word start time drift detected: %f vs %f",
                                audio_time,
                                word_start,
                            )
                            await ws.close()
                            return
                    elif data["type"] == "EndWord":
                        audio_window.push_end_word(end_time=data["stop_time"])
                    elif data["type"] == "Marker":
                        pass
                    elif data["type"] == "Ready":
                        pass
                    else:
                        logging.warning("Received unknown message type: %s", data)

                events = audio_window.get_events()
                for event in events:
                    self._output_queue.put_nowait(event)

                if needs_flush:
                    self._process_queue.put_nowait(FLUSH_FRAME)

        async def send_task(ws: aiohttp.ClientWebSocketResponse) -> None:
            nonlocal audio_samples
            while True:
                if ws.closed:
                    break
                item = await self._process_queue.get()
                if item is None:
                    return
                audio_window.push_audio(item)

                concatted_floats = cast(
                    list[float], item.data_24000hz.fp32.flatten().tolist()
                )
                audio_samples += item.data_24000hz.sample_count
                if len(concatted_floats) == 0:
                    # logging.warning("Received empty audio frame, skipping")
                    continue
                msg = {
                    "type": "Audio",
                    "pcm": concatted_floats,
                }
                packed = cast(
                    bytes, msgpack.packb(msg, use_bin_type=True, use_single_float=True)
                )
                await ws.send_bytes(packed)
                self._process_queue.task_done()

        async def keepalive_task(ws: aiohttp.ClientWebSocketResponse) -> None:
            while not self._closed:
                await asyncio.sleep(2)
                if ws.closed:
                    break
                await ws.ping()

        async with aiohttp.ClientSession() as session:
            async with session.ws_connect(
                f"ws://localhost:{self._port}/api/asr-streaming",
                headers={"kyutai-api-key": "open_token"},
            ) as ws:  # Adjust port as needed
                await asyncio.gather(
                    rec_task(ws),
                    send_task(ws),
                    keepalive_task(ws),
                )

    def __aiter__(self):
        return self

    async def __anext__(self) -> STTEvent:
        event = await self._output_queue.get()
        if event is None:
            raise StopAsyncIteration
        return event

    def endpoint_cooldown(self, prob, last_word) -> None:
        """
        Signal the end of the audio stream.
        """
        self._process_queue.put_nowait(None)


class AudioWindow:
    def __init__(self):
        # These come from kyutai's implemention. Attach time is for speaking->not speaking. Release time is for not speaking->speaking.
        # So an initial value of 1.0 means we are not speaking, and 0.0 means we are speaking.
        self._pause_prediction = ExponentialMovingAverage(
            attack_time=0.4, release_time=0.1, initial_value=1.0
        )
        self._first_word_start_time: float | None = None
        self._end_word_start_time: float | None = None
        self._speaking_start_idx: int | None = None

        self._buffer: list[AudioFrame] = []
        self._transcription = ""
        self._id = short_uuid()
        self._output_events: list[STTEvent] = []
        self._step_idx = 0
        self._end_cooldown_idx: int | None = None

    @property
    def paused_detected(self):
        return self._pause_prediction.value > 0.6

    def push_audio(self, buffer: AudioFrame) -> None:
        self._buffer.append(buffer)

    def push_word(self, *, word: str, start_time: float) -> None:
        delta = ""
        new_tran = False
        if not self._transcription:
            new_tran = True
            delta = word
        else:
            delta = " " + word

        self._transcription += delta

        if new_tran:
            self._first_word_start_time = start_time
            self._speaking_start_idx = self._step_idx
            self._pause_prediction.value = 0
            self._output_events.append(
                STTEvent_SpeechStarted(
                    id=self._id,
                )
            )

        self._output_events.append(
            STTEvent_Transcription(
                id=self._id,
                delta_text=delta,
                running_text=self._transcription,
            )
        )

    def push_end_word(self, end_time: float) -> None:
        if not self._first_word_start_time:
            # The last end word doesn't seem to be coming so we skip it.
            return

        self._end_word_start_time = end_time

    def push_step(self, end_prob: float):
        self._step_idx += 1
        self._pause_prediction.update(dt=1 / STEPS_PER_SECOND, new_value=end_prob)

        self._prune_old_frames()

        if (
            self.paused_detected
            and self._end_cooldown_idx is None
            and self._speaking_start_idx is not None
        ):
            self._end_cooldown_idx = self._step_idx + int(
                STEPS_PER_SECOND * COOLDOWN_SECONDS
            )
            return True

        if (
            self._end_cooldown_idx is not None
            and self._step_idx >= self._end_cooldown_idx
        ):
            if self._transcription:
                self._output_events.append(
                    STTEvent_EndOfTurn(id=self._id, clip=self._get_clip())
                )
            self._end_cooldown_idx = None
            self._speaking_start_idx = None
            self._first_word_start_time = None
            self._end_word_start_time = None
            self._buffer = []
            self._transcription = ""
            self._id = short_uuid()

        return False

    def _prune_old_frames(self) -> None:
        if not self._speaking_start_idx:
            total_duration = 0
            for b in self._buffer:
                if id(b) == id(FLUSH_FRAME):
                    continue
                total_duration += b.original_data.duration

            # Account for STT processing time. TODO: Probably can do this properly with word timestamps.
            while total_duration > PRE_BUFFER_SECONDS and len(self._buffer) > 1:
                first = self._buffer.pop(0)
                total_duration -= first.original_data.duration

        total_duration = 0
        for b in self._buffer:
            total_duration += b.original_data.duration

    def _get_clip(self) -> AudioClip:
        if (
            not self._end_word_start_time
            or not self._first_word_start_time
            or not self._speaking_start_idx
        ):
            logging.warning(
                "End word start or first word start is None, returning empty clip."
            )
            return AudioClip(audio=[], transcription=self._transcription)

        first_word_seconds = self._end_word_start_time - self._first_word_start_time
        actual_start_idx = (
            self._speaking_start_idx - first_word_seconds * STEPS_PER_SECOND
        )
        actual_buffer_duration = (
            (self._step_idx - actual_start_idx) * (1.0 / STEPS_PER_SECOND) + 0.75
        )  # Add a bit of buffer to account for STT processing time. TODO: can probably calculate this properly with markers.
        # take the last buffers that are within the actual buffer duration
        res: list[AudioFrame] = []
        i = len(self._buffer) - 1
        while actual_buffer_duration > 0 and i > 0:
            res.append(self._buffer[i])
            actual_buffer_duration -= self._buffer[i].original_data.duration
            i -= 1

        res.reverse()
        res = [b for b in res if id(b) != id(FLUSH_FRAME)]

        return AudioClip(
            audio=res,
            transcription=self._transcription,
        )

    @property
    def step_time(self):
        return float(self._step_idx * (1.0 / STEPS_PER_SECOND))

    def get_events(self) -> list[STTEvent]:
        res = self._output_events
        self._output_events = []
        return res
