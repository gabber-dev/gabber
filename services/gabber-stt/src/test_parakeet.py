import asyncio
import threading
import time
import queue

import numpy as np
import pyaudio
from core import AudioInferenceSession
from lib import vad, stt

CHUNK = 16000
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000

p = pyaudio.PyAudio()


class TestClient:
    def __init__(self, inference_session: AudioInferenceSession):
        self._inference_session = inference_session
        self._stream = p.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=RATE,
            input=True,
            frames_per_buffer=CHUNK,
        )
        self._input_queue = queue.Queue[bytes]()

    def _stream_thread(self):
        while True:
            data = self._stream.read(CHUNK, exception_on_overflow=False)
            self._input_queue.put(data)
            time.sleep(0.001)

    async def run(self):
        thread = threading.Thread(target=self._stream_thread)
        thread.start()

        remainder = np.zeros(0, dtype=np.int16)
        while True:
            data = await asyncio.get_event_loop().run_in_executor(
                None, self._input_queue.get
            )
            remainder = np.concatenate((remainder, np.frombuffer(data, dtype=np.int16)))
            for i in range(
                0, remainder.shape[0], self._inference_session.new_audio_size
            ):
                segment = remainder[i : i + self._inference_session.new_audio_size]
                if segment.shape[0] < self._inference_session.new_audio_size:
                    remainder = segment
                    break
                res = await self._inference_session.inference(segment)

            remainder_size = remainder.shape[0] % self._inference_session.new_audio_size
            remainder = remainder[-remainder_size:]


async def main():
    vad_engine = vad.VADInferenceEngine(inference_impl=vad.silero.SileroVADInference())
    await vad_engine.initialize()
    vad_session = vad_engine.create_session()

    stt_engine = stt.STTInferenceEngine(
        inference_impl=stt.parakeet.ParakeetSTTInference(chunk_secs=2)
    )
    await stt_engine.initialize()
    stt_session = stt_engine.create_session()

    tc = TestClient(stt_session)
    await tc.run()


if __name__ == "__main__":
    asyncio.run(main())
