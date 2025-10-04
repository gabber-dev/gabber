import asyncio
import queue
import threading
from typing import Protocol
from dataclasses import dataclass

import numpy as np


class EndOfTurn:
    def __init__(self, *, eot_inference: "EOTInference", tick_s: float):
        self._eot_inference = eot_inference
        self._eot_batcher = EOTInferenceBatcher(eot_inference=eot_inference)
        self._tick_s = tick_s

    @property
    def sample_rate(self) -> int:
        return self._eot_inference.sample_rate

    def create_session(self) -> "EOTSession":
        return EOTSession(
            batcher=self._eot_batcher, chunk_size=int(self._tick_s * self.sample_rate)
        )


class EOTInference(Protocol):
    @property
    def chunk_size(self) -> int: ...

    @property
    def sample_rate(self) -> int: ...

    def inference(self, audio_chunks: np.typing.NDArray[np.int16]) -> list[float]: ...


@dataclass
class EOTInferenceBatcherPromise:
    audio: np.typing.NDArray[np.int16]
    fut: asyncio.Future[float]


class EOTInferenceBatcher:
    def __init__(self, *, eot_inference: EOTInference, batch_size: int = 8):
        self._batch_size = batch_size
        self._eot_inference = eot_inference
        self._fut_lookup: dict[int, asyncio.Future[float]] = {}
        self._run_thread = threading.Thread(target=self._run)
        self._batch = queue.Queue[EOTInferenceBatcherPromise](maxsize=1024)
        self._run_thread.start()

    @property
    def chunk_size(self) -> int:
        return self._eot_inference.chunk_size

    @property
    def sample_rate(self) -> int:
        return self._eot_inference.sample_rate

    def _run(self):
        while True:
            batch_arr = np.empty(
                (self._batch_size, self._eot_inference.chunk_size),
                dtype=np.int16,
            )
            futs: list[asyncio.Future[float]] = []
            while len(futs) < self._batch_size:
                try:
                    prom = self._batch.get(timeout=0.05)
                    batch_arr[len(futs)] = prom.audio
                    futs.append(prom.fut)
                except queue.Empty:
                    break

            if len(futs) == 0:
                continue

            results = self._eot_inference.inference(batch_arr)

            for i, fut in enumerate(futs):
                fut.set_result(results[i])

    async def inference(self, audio: np.typing.NDArray[np.int16]) -> float:
        try:
            fut = asyncio.Future[float]()
            self._batch.put_nowait(EOTInferenceBatcherPromise(audio=audio, fut=fut))
            res = await fut
            return res
        except queue.Full:
            raise RuntimeError("EOT inference batcher queue is full")
        except Exception as e:
            raise RuntimeError("EOT inference batcher failed") from e


class EOTSession:
    def __init__(self, *, batcher: EOTInferenceBatcher, chunk_size: int):
        self._batcher = batcher
        self._chunk_size = chunk_size
        self._context = np.zeros(batcher.chunk_size - chunk_size, dtype=np.int16)

    @property
    def chunk_size(self) -> int:
        return self._chunk_size

    @property
    def sample_rate(self) -> int:
        return self._batcher.sample_rate

    async def eot(self, audio_chunk: np.typing.NDArray[np.int16]) -> float:
        if len(audio_chunk) != self.chunk_size:
            raise ValueError(
                f"Invalid audio chunk size: {len(audio_chunk)}, expected {self.chunk_size}"
            )
        chunk = np.concatenate((self._context, audio_chunk))
        prob = await self._batcher.inference(chunk)
        self._context = chunk[-(self._batcher.chunk_size - self.chunk_size) :]
        return prob
