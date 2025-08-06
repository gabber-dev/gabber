from kittentts import KittenTTS
from fastapi import FastAPI, Body, Response
from starlette.concurrency import run_in_threadpool
from pydantic import BaseModel
import numpy as np
import uvicorn

m = KittenTTS("KittenML/kitten-tts-nano-0.1")

app = FastAPI()


class TTSRequest(BaseModel):
    text: str
    voice: str


@app.post("/tts")
async def tts(request: TTSRequest = Body(...)):
    audio = await run_in_threadpool(
        lambda: m.generate(request.text, voice=request.voice)
    )

    # Convert to 16-bit PCM (2 bytes per sample, ensuring byte length is divisible by 2)
    audio_int16 = (audio * 32767).astype(np.int16)
    audio_bytes = audio_int16.tobytes()
    if len(audio_bytes) % 2 != 0:
        audio_bytes += b"\x00"

    return Response(content=audio_bytes, media_type="audio/l16;rate=24000")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=80)
