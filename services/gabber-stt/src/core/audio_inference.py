import asyncio
import logging
import time
import queue
import threading
from dataclasses import dataclass
from typing import Any, Protocol, Generic, TypeVar
from .audio_window import AudioWindow

import numpy as np

RESULT = TypeVar("RESULT")


class AudioInferenceEngine(Generic[RESULT]):
    def __init__(
        self,
        *,
        inference_impl: "AudioInference",
        batch_size: int = 32,
        batch_timeout: float = 0.01,
    ):
        self.inference_impl = inference_impl
        self.batcher = AudioInferenceBatcher(
            inference_impl=inference_impl,
            batch_size=batch_size,
            batch_timeout=batch_timeout,
        )

    @property
    def sample_rate(self) -> int:
        return self.inference_impl.sample_rate

    def create_session(self) -> "AudioInferenceSession[RESULT]":
        return AudioInferenceSession(batcher=self.batcher)

    async def initialize(self) -> None:
        await self.inference_impl.initialize()
        self.batcher.start()


class AudioInferenceSession(Generic[RESULT]):
    def __init__(self, *, batcher: "AudioInferenceBatcher"):
        self.batcher = batcher
        self.audio_window = AudioWindow(
            max_length_s=(
                self.batcher._inference_impl.full_audio_size / self.batcher.sample_rate
            )
            * 2,
            sample_rates=[self.batcher.sample_rate],
            input_sample_rate=self.batcher.sample_rate,
        )
        self._state: Any = None
        self._curs = 0

    @property
    def new_audio_size(self) -> int:
        return self.batcher._inference_impl.new_audio_size

    @property
    def sample_rate(self) -> int:
        return self.batcher.sample_rate

    async def inference(self, audio: np.typing.NDArray[np.int16]) -> RESULT:
        if audio.ndim != 1:
            raise ValueError(f"Invalid audio shape: {audio.shape}, must be 1D")

        if audio.shape[0] != self.new_audio_size:
            raise ValueError(
                f"Invalid audio size: {audio.shape[0]}, must be {self.new_audio_size}"
            )

        self.audio_window.push_audio(audio=audio)
        self._curs += audio.shape[0]
        inference_audio = self.audio_window.get_segment(
            sample_rate=self.batcher.sample_rate,
            start_cursor=max(
                0, self._curs - self.batcher._inference_impl.full_audio_size
            ),
            end_cursor=self._curs,
        )

        num_samples = inference_audio.shape[0]

        if inference_audio.shape[0] != self.batcher._inference_impl.full_audio_size:
            inference_audio = np.pad(
                inference_audio,
                (
                    0,
                    self.batcher._inference_impl.full_audio_size
                    - inference_audio.shape[0],
                ),
            )

        res = await self.batcher.inference(inference_audio, self._state, num_samples)
        self._state = res.state
        return res.result

    def reset(self):
        self._state = None
        self._curs = 0


@dataclass
class AudioInferenceBatcherPromise(Generic[RESULT]):
    audio: np.typing.NDArray[np.int16]
    prev_state: Any | None
    num_samples: int
    fut: "asyncio.Future[AudioInferenceInternalResult[RESULT]]"


class AudioInferenceBatcher(Generic[RESULT]):
    def __init__(
        self,
        *,
        inference_impl: "AudioInference[RESULT]",
        batch_size: int = 32,
        batch_timeout: float = 0.01,
    ):
        self._batch_timeout = batch_timeout
        self._batch_size = batch_size
        self._inference_impl = inference_impl
        self._fut_lookup: "dict[int, asyncio.Future[AudioInferenceInternalResult[RESULT]]]" = {}
        self._run_thread = threading.Thread(target=self._run)
        self._batch = queue.Queue[AudioInferenceBatcherPromise](maxsize=1024)
        self._loop = asyncio.get_event_loop()

    @property
    def sample_rate(self) -> int:
        return self._inference_impl.sample_rate

    def _run(self):
        while True:
            batch_arr = np.empty(
                (self._batch_size, self._inference_impl.full_audio_size),
                dtype=np.int16,
            )
            prev_states: list[Any] = []
            num_samples: list[int] = []
            futs: list[asyncio.Future[AudioInferenceInternalResult[RESULT]]] = []
            while len(futs) < self._batch_size:
                try:
                    prom = self._batch.get(timeout=self._batch_timeout)
                    num_samples.append(prom.num_samples)
                    batch_arr[len(futs)] = prom.audio
                    prev_states.append(prom.prev_state)
                    futs.append(prom.fut)
                except queue.Empty:
                    break
                except Exception:
                    logging.error("Error in STT inference batcher", exc_info=True)

            if len(futs) == 0:
                continue

            req = AudioInferenceRequest(
                audio_batch=batch_arr[: len(futs)],
                prev_states=prev_states,
                num_samples=num_samples,
            )
            results = self._inference_impl.inference(req)

            for i, fut in enumerate(futs):
                self._loop.call_soon_threadsafe(fut.set_result, results[i])

    def start(self):
        self._run_thread.start()

    async def inference(
        self,
        audio: np.typing.NDArray[np.int16],
        prev_state: Any | None,
        num_samples: int,
    ) -> "AudioInferenceInternalResult[RESULT]":
        try:
            fut = asyncio.Future[AudioInferenceInternalResult[RESULT]]()
            self._batch.put_nowait(
                AudioInferenceBatcherPromise(
                    audio=audio,
                    prev_state=prev_state,
                    fut=fut,
                    num_samples=num_samples,
                )
            )
            res = await fut
            return res
        except queue.Full:
            raise RuntimeError("STT inference batcher queue is full")
        except Exception as e:
            raise RuntimeError("STT inference batcher failed") from e


class AudioInference(Protocol, Generic[RESULT]):
    def inference(
        self, input: "AudioInferenceRequest"
    ) -> "list[AudioInferenceInternalResult[RESULT]]": ...

    @property
    def new_audio_size(self) -> int: ...

    @property
    def full_audio_size(self) -> int: ...

    @property
    def sample_rate(self) -> int: ...

    async def initialize(self) -> None: ...


@dataclass
class AudioInferenceRequest:
    audio_batch: np.typing.NDArray[np.int16]
    prev_states: list[Any]
    num_samples: list[int]


@dataclass
class AudioInferenceInternalResult(Generic[RESULT]):
    state: Any
    result: RESULT
