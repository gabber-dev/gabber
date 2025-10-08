import asyncio
import threading
import time
import queue

import numpy as np
import pyaudio
from core import AudioInferenceSession
from lib import vad, stt
import numpy as np
from nemo.collections.asr.models import EncDecMultiTaskModel
from tqdm import tqdm
from functools import partialmethod

tqdm.__init__ = partialmethod(tqdm.__init__, disable=True)

CHUNK = 3200
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000

model = EncDecMultiTaskModel.from_pretrained("nvidia/canary-1b-v2")

p = pyaudio.PyAudio()


class TestClient:
    def __init__(self):
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

    async def run(self):
        thread = threading.Thread(target=self._stream_thread)
        thread.start()

        remainder = np.zeros(0, dtype=np.int16)
        while True:
            data = await asyncio.get_event_loop().run_in_executor(
                None, self._input_queue.get
            )
            remainder = np.concatenate((remainder, np.frombuffer(data, dtype=np.int16)))

            start_time = time.time()
            transcriptions = model.transcribe(
                audio=[remainder.astype(np.float32) / 32768.0],
                batch_size=1,
                task="asr",  # For automatic speech recognition
                source_lang="en",  # Source language (set equal to target for ASR)
                target_lang="en",  # Target language
                pnc="yes",  # Enable punctuation and capitalization ("yes" or "no")
            )
            print("NEIL res", transcriptions[0], time.time() - start_time)


async def main():
    tc = TestClient()
    await tc.run()


if __name__ == "__main__":
    asyncio.run(main())
