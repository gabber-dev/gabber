import asyncio
import logging
import queue
import threading
from dataclasses import dataclass
from typing import Any, Protocol

import numpy as np


class STT:
    def __init__(self, *, stt_inference: "STTInference"):
        self._stt_inference = stt_inference
        self._stt_inference_batcher = STTInferenceBatcher(stt_inference=stt_inference)

    @property
    def sample_rate(self) -> int:
        return self._stt_inference.sample_rate

    def create_session(self) -> "STTSession":
        return STTSession(batcher=self._stt_inference_batcher)


class STTSession:
    def __init__(self, *, batcher: "STTInferenceBatcher"):
        self._batcher = batcher
        self._audio = np.zeros(batcher.inference_window_size, dtype=np.int16)
        self._state: Any = None

    @property
    def new_audio_size(self) -> int:
        return self._batcher.stt_inference.new_audio_size

    @property
    def sample_rate(self) -> int:
        return self._batcher.sample_rate

    async def transcribe(
        self, audio: np.typing.NDArray[np.int16]
    ) -> "STTInferenceResult":
        if audio.ndim != 1:
            raise ValueError(f"Invalid audio shape: {audio.shape}, must be 1D")

        if audio.shape[0] != self.new_audio_size:
            raise ValueError(
                f"Invalid audio size: {audio.shape[0]}, must be {self.new_audio_size}"
            )

        res = await self._batcher.transcribe(audio, None)
        self._state = res.state
        return STTInferenceResult.from_internal(res)

    def eos(self):
        pass


@dataclass
class STTInferenceBatcherPromise:
    audio: np.typing.NDArray[np.int16]
    decoder_states: Any | None
    fut: asyncio.Future["STTInternalInferenceResult"]


class STTInferenceBatcher:
    def __init__(self, *, stt_inference: "STTInference", batch_size: int = 32):
        self._batch_size = batch_size
        self.stt_inference = stt_inference
        self._fut_lookup: dict[int, asyncio.Future["STTInternalInferenceResult"]] = {}
        self._run_thread = threading.Thread(target=self._run)
        self._batch = queue.Queue[STTInferenceBatcherPromise](maxsize=1024)
        self._run_thread.start()

    @property
    def inference_window_size(self) -> int:
        return (
            self.stt_inference.left_context_size
            + self.stt_inference.new_audio_size
            + self.stt_inference.right_context_size
        )

    @property
    def sample_rate(self) -> int:
        return self.stt_inference.sample_rate

    def _run(self):
        while True:
            batch_arr = np.empty(
                (self._batch_size, self.inference_window_size), dtype=np.int16
            )
            prev_states: list[Any | None] = []
            futs: list[asyncio.Future[STTInternalInferenceResult]] = []
            while len(futs) < self._batch_size:
                try:
                    prom = self._batch.get(timeout=0.01)
                    batch_arr[len(futs)] = prom.audio
                    prev_states.append(prom.decoder_states)
                    futs.append(prom.fut)
                except queue.Empty:
                    break

            if len(futs) == 0:
                continue

            req = STTInferenceRequest(
                audio_batch=batch_arr[: len(futs)], prev_states=prev_states
            )
            results = self.stt_inference.inference(req)

            for i, fut in enumerate(futs):
                fut.set_result(results[i])

    async def transcribe(
        self, audio: np.typing.NDArray[np.int16], decoder_states: Any | None
    ) -> "STTInternalInferenceResult":
        try:
            fut = asyncio.Future[STTInternalInferenceResult]()
            self._batch.put_nowait(
                STTInferenceBatcherPromise(
                    audio=audio, decoder_states=decoder_states, fut=fut
                )
            )
            res = await fut
            return res
        except queue.Full:
            raise RuntimeError("VAD inference batcher queue is full")
        except Exception as e:
            raise RuntimeError("VAD inference batcher failed") from e


class STTInference(Protocol):
    def inference(
        self, input: "STTInferenceRequest"
    ) -> list["STTInternalInferenceResult"]: ...

    @property
    def new_audio_size(self) -> int: ...

    @property
    def left_context_size(self) -> int: ...

    @property
    def right_context_size(self) -> int: ...

    @property
    def sample_rate(self) -> int: ...


@dataclass
class STTInferenceRequest:
    audio_batch: np.typing.NDArray[np.int16]
    prev_states: list[Any]


@dataclass
class STTResultWord:
    word: str
    start_cursor: float
    end_cursor: float


@dataclass
class STTInternalInferenceResult:
    state: Any
    transcription: str
    start_cursor: float
    end_cursor: float
    words: list[STTResultWord]


@dataclass
class STTInferenceResult:
    transcription: str
    words: list[STTResultWord]
    start_cursor: float
    end_cursor: float

    @classmethod
    def from_internal(
        cls, internal: STTInternalInferenceResult
    ) -> "STTInferenceResult":
        return cls(
            transcription=internal.transcription,
            words=internal.words,
            start_cursor=internal.start_cursor,
            end_cursor=internal.end_cursor,
        )
