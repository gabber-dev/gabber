import asyncio
import logging
import queue
import threading
from dataclasses import dataclass
from typing import Protocol, Generic, TypeVar

import numpy as np

logger = logging.getLogger(__name__)

CONTEXT_SIZE = 64


class VADInference(Protocol):
    @property
    def chunk_size(self) -> int: ...

    @property
    def sample_rate(self) -> int: ...

    def inference(self, audio_chunks: np.typing.NDArray[np.int16]) -> list[float]: ...


class VAD:
    def __init__(self, *, vad_inference: VADInference):
        self._vad_inference = vad_inference
        self._vad_batcher = VADInferenceBatcher(vad_inference=vad_inference)

    @property
    def sample_rate(self) -> int:
        return self._vad_inference.sample_rate

    def create_session(self) -> "VADSession":
        return VADSession(batcher=self._vad_batcher)


@dataclass
class VADInferenceBatcherPromise:
    audio: np.typing.NDArray[np.int16]
    fut: asyncio.Future[float]


class VADInferenceBatcher:
    def __init__(self, *, vad_inference: VADInference, batch_size: int = 32):
        self._batch_size = batch_size
        self._vad_inference = vad_inference
        self._fut_lookup: dict[int, asyncio.Future[float]] = {}
        self._run_thread = threading.Thread(target=self._run)
        self._batch = queue.Queue[VADInferenceBatcherPromise](maxsize=1024)
        self._run_thread.start()

    @property
    def chunk_size(self) -> int:
        return self._vad_inference.chunk_size

    @property
    def sample_rate(self) -> int:
        return self._vad_inference.sample_rate

    def _run(self):
        while True:
            batch_arr = np.empty(
                (self._batch_size, self._vad_inference.chunk_size), dtype=np.int16
            )
            futs: list[asyncio.Future[float]] = []
            while len(futs) < self._batch_size:
                try:
                    prom = self._batch.get(timeout=0.01)
                    batch_arr[len(futs)] = prom.audio
                    futs.append(prom.fut)
                except queue.Empty:
                    break

            if len(futs) == 0:
                continue

            results = self._vad_inference.inference(batch_arr)

            for i, fut in enumerate(futs):
                fut.set_result(results[i])

    async def inference(self, audio: np.typing.NDArray[np.int16]) -> float:
        try:
            fut = asyncio.Future[float]()
            self._batch.put_nowait(VADInferenceBatcherPromise(audio=audio, fut=fut))
            res = await fut
            return res
        except queue.Full:
            raise RuntimeError("VAD inference batcher queue is full")
        except Exception as e:
            raise RuntimeError("VAD inference batcher failed") from e


class VADSession:
    def __init__(self, *, batcher: VADInferenceBatcher):
        self._batcher = batcher
        self._context = np.zeros(CONTEXT_SIZE, dtype=np.int16)

    @property
    def chunk_size(self) -> int:
        return self._batcher.chunk_size - CONTEXT_SIZE

    @property
    def sample_rate(self) -> int:
        return self._batcher.sample_rate

    async def has_voice(self, audio_chunk: np.typing.NDArray[np.int16]) -> float:
        if len(audio_chunk) != self.chunk_size:
            raise ValueError(
                f"Invalid audio chunk size: {len(audio_chunk)}, expected {self.chunk_size}"
            )

        chunk = np.concatenate((self._context, audio_chunk))
        prob = await self._batcher.inference(chunk)
        self._context = chunk[-CONTEXT_SIZE:]
        return prob
