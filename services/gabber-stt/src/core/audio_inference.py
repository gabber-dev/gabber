import asyncio
import time
import queue
import threading
import wave
from dataclasses import dataclass
from typing import Any, Protocol, Generic, TypeVar

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

    def create_session(self) -> "AudioInferenceSession":
        return AudioInferenceSession(batcher=self.batcher)

    async def initialize(self) -> None:
        await self.inference_impl.initialize()


class AudioInferenceSession(Generic[RESULT]):
    def __init__(self, *, batcher: "AudioInferenceBatcher"):
        self.batcher = batcher
        self._audio = np.zeros(batcher._inference_impl.full_audio_size, dtype=np.int16)
        self._state: Any = None
        self._last_inference_time = time.perf_counter()
        self._idx = 0

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

        self._audio = np.concatenate((self._audio, audio))

        if self._audio.shape[0] > self.batcher._inference_impl.full_audio_size:
            self._audio = self._audio[-self.batcher._inference_impl.full_audio_size :]

        with wave.open(f"debug_{self._idx}.wav", "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(self.sample_rate)
            wf.writeframes(audio.tobytes())
        self._idx += 1
        res = await self.batcher.inference(self._audio, None)
        self._state = res.state
        return res.result

    def eos(self):
        pass


@dataclass
class AudioInferenceBatcherPromise(Generic[RESULT]):
    audio: np.typing.NDArray[np.int16]
    decoder_states: Any | None
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
        self._run_thread.start()

    @property
    def sample_rate(self) -> int:
        return self._inference_impl.sample_rate

    def _run(self):
        while True:
            batch_arr = np.empty(
                (self._batch_size, self._inference_impl.full_audio_size),
                dtype=np.int16,
            )
            prev_states: list[Any | None] = []
            futs: list[asyncio.Future[AudioInferenceInternalResult[RESULT]]] = []
            while len(futs) < self._batch_size:
                try:
                    prom = self._batch.get(timeout=self._batch_timeout)
                    batch_arr[len(futs)] = prom.audio
                    prev_states.append(prom.decoder_states)
                    futs.append(prom.fut)
                except queue.Empty:
                    break
                except Exception:
                    print("STT Inference batcher failed to get from queue")

            if len(futs) == 0:
                continue

            req = AudioInferenceRequest(
                audio_batch=batch_arr[: len(futs)], prev_states=prev_states
            )
            results = self._inference_impl.inference(req)

            for i, fut in enumerate(futs):
                self._loop.call_soon_threadsafe(fut.set_result, results[i])

    async def inference(
        self, audio: np.typing.NDArray[np.int16], decoder_states: Any | None
    ) -> "AudioInferenceInternalResult[RESULT]":
        try:
            fut = asyncio.Future[AudioInferenceInternalResult[RESULT]]()
            self._batch.put_nowait(
                AudioInferenceBatcherPromise(
                    audio=audio, decoder_states=decoder_states, fut=fut
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


@dataclass
class AudioInferenceInternalResult(Generic[RESULT]):
    state: Any
    result: RESULT
