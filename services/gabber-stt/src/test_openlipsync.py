import asyncio
import wave
import numpy as np
from lib.lipsync.openlipsync import OpenLipSyncInference
from lib.lipsync import Viseme
from core import AudioInferenceRequest
import logging


async def main():
    audio_bytes = b""
    with wave.open("src/test.wav", "rb") as wf:
        n_frames = wf.getnframes()
        audio_bytes = wf.readframes(n_frames)

    inf = OpenLipSyncInference()
    await inf.initialize()
    np_bytes = np.expand_dims(np.frombuffer(audio_bytes, dtype=np.int16), axis=0)
    req = AudioInferenceRequest(
        audio_batch=np_bytes, prev_states=[None], num_samples=np_bytes.shape[1]
    )
    result = await asyncio.get_event_loop().run_in_executor(None, inf.inference, req)
    visemes = [
        r.max_viseme_prob.viseme
        for r in result[0].result
        if r.max_viseme_prob.viseme != Viseme.SILENCE
    ]
    logging.info(f"Visemes: {visemes}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
