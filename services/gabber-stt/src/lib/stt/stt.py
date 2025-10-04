import asyncio
import queue
import threading
from dataclasses import dataclass
from typing import Any, Protocol

import numpy as np


class STT(Protocol):
    @property
    def sample_rate(self) -> int: ...

    def create_session(self) -> "STTSession": ...


class STTSession(Protocol):
    def accept_audio(self, audio: bytes) -> None: ...

    def eos(self) -> str: ...

    def push_audio(self, audio: bytes) -> None:
        self.accept_audio(audio)


@dataclass
class STTInferenceBatcherPromise:
    audio: np.typing.NDArray[np.int16]
    decoder_states: Any | None
    fut: asyncio.Future["STTInferenceResult"]


class STTInferenceBatcher:
    def __init__(self, *, stt_inference: "STTInference", batch_size: int = 32):
        self._batch_size = batch_size
        self._stt_inference = stt_inference
        self._fut_lookup: dict[int, asyncio.Future["STTInferenceResult"]] = {}
        self._run_thread = threading.Thread(target=self._run)
        self._batch = queue.Queue[STTInferenceBatcherPromise](maxsize=1024)
        self._run_thread.start()

    @property
    def chunk_size(self) -> int:
        return self._stt_inference.chunk_size

    @property
    def sample_rate(self) -> int:
        return self._stt_inference.sample_rate

    def _run(self):
        while True:
            batch_arr = np.empty(
                (self._batch_size, self._stt_inference.chunk_size), dtype=np.int16
            )
            decoder_states: list[Any | None] = []
            futs: list[asyncio.Future[STTInferenceResult]] = []
            while len(futs) < self._batch_size:
                try:
                    prom = self._batch.get(timeout=0.01)
                    batch_arr[len(futs)] = prom.audio
                    decoder_states.append(prom.decoder_states)
                    futs.append(prom.fut)
                except queue.Empty:
                    break

            if len(futs) == 0:
                continue

            results = self._stt_inference.inference(
                batch_arr[: len(futs)], decoder_states
            )

            for i, fut in enumerate(futs):
                fut.set_result(results[i])

    async def inference(
        self, audio: np.typing.NDArray[np.int16], decoder_states: Any | None
    ) -> "STTInferenceResult":
        try:
            fut = asyncio.Future[STTInferenceResult]()
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
        self, audio_batch: np.typing.NDArray[np.int16], decoder_states: list[Any | None]
    ) -> list["STTInferenceResult"]: ...

    @property
    def chunk_size(self) -> int: ...

    @property
    def sample_rate(self) -> int: ...


@dataclass
class STTResultWord:
    word: str
    start_cursor: float
    end_cursor: float


@dataclass
class STTInferenceResult:
    decoder_state: Any
    transcription: str
    start_cursor: float
    end_cursor: float
    words: list[STTResultWord]
