import asyncio
import logging
import queue
import threading
import time
from dataclasses import dataclass
from typing import Protocol

import numpy as np

logger = logging.getLogger(__name__)


class VADInference(Protocol):
    @property
    def inference_chunk_sample_count(self) -> int: ...

    @property
    def sample_rate(self) -> int: ...

    def inference(self, audio_chunks: np.typing.NDArray[np.int16]) -> list[float]: ...


class VAD:
    def __init__(self, *, vad_inference: VADInference):
        self._initialized = False
        self._vad_inference = vad_inference
        self._vad_batcher = VADInferenceBatcher(vad_inference=vad_inference)
        self._closed = False

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
    def __init__(self, *, vad_inference: VADInference, batch_size: int = 64):
        self._batch_size = batch_size
        self._vad_inference = vad_inference
        self._fut_lookup: dict[int, asyncio.Future[float]] = {}
        self._run_thread = threading.Thread(target=self._run)
        self._batch = queue.Queue[VADInferenceBatcherPromise](maxsize=1024)
        self._run_thread.start()

    @property
    def chunk_size(self) -> int:
        return self._vad_inference.inference_chunk_sample_count

    def _run(self):
        while True:
            time.sleep(0.1)
            batch_arr = np.empty(
                (self._batch_size, self._vad_inference.inference_chunk_sample_count),
                dtype=np.int16,
            )
            futs: list[asyncio.Future[float]] = []
            while len(futs) < self._batch_size and not self._batch.not_empty:
                prom = self._batch.get()
                batch_arr = np.concatenate((batch_arr, prom.audio.reshape(1, -1)))
                futs.append(prom.fut)

            print("NEIL got here", batch_arr.shape, len(futs))  # --- IGNORE ---

            results = self._vad_inference.inference(batch_arr)
            if len(results) != len(futs):
                logger.error("VAD batcher returned mismatched result count")
                for fut in futs:
                    if not fut.done():
                        fut.set_exception(
                            RuntimeError("VAD batcher returned mismatched result count")
                        )
                continue

            for i, fut in enumerate(futs):
                if not fut.done():
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

    async def has_voice(self, audio_chunk: np.typing.NDArray[np.int16]) -> float:
        chunks = []
        chunk_size = self._batcher.chunk_size
        for i in range(0, len(audio_chunk), chunk_size):
            chunk = audio_chunk[i : i + chunk_size]
            if len(chunk) < chunk_size:
                chunk = np.pad(chunk, (0, chunk_size - len(chunk)), mode="constant")
            chunks.append(chunk)

        results = await asyncio.gather(*[self._batcher.inference(c) for c in chunks])
        print("NEIL VAD results", results)  # --- IGNORE ---
        return max(results)
