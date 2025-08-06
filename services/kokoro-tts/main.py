from fastapi import FastAPI, Body
from fastapi.responses import StreamingResponse
from kokoro import KPipeline
import numpy as np
import torch
import uvicorn

app = FastAPI()

pipeline = KPipeline(lang_code="a")


@app.post("/tts")
async def tts(text: str = Body(...)):
    generator = pipeline(text, voice="af_heart")

    def stream_gen():
        for _, (_, _, audio) in enumerate(generator):
            # Assuming audio is a numpy float array normalized between -1 and 1
            audio_int16 = (audio * 32767).astype(np.dtype("<i2"))
            yield audio_int16.tobytes()

    return StreamingResponse(stream_gen(), media_type="audio/l16;rate=24000")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
