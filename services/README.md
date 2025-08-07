# Gabber Services

This repository contains individual AI-powered services used within the Gabber ecosystem.
Each service has its own `start.sh` script to simplify building and running the service in a Docker container.
You must run the service as specified below for the corresponding Gabber node to work on your machine.

> **TL;DR**
> - `joycaption` → image captioning via vLLM (OpenAI-compatible API) on **:7002**
> - `kitten-tts` → text-to-speech FastAPI that returns raw 24kHz 16‑bit PCM on **:7003**
> - `kyutai-stt` → Moshi-based STT worker (GPU/CUDA required)

---

## Table of Contents
- [Prerequisites](#prerequisites)
- [Directory Layout](#directory-layout)
- [Quick Start](#quick-start)
- [Services](#services)
  - [joycaption](#1-joycaption)
  - [kitten-tts](#2-kitten-tts)
  - [kyutai-stt](#3-kyutai-stt)
- [Development Notes](#development-notes)
- [Troubleshooting](#troubleshooting)
- [License](#license)

---

## Prerequisites

- **Docker** (and **NVIDIA Container Toolkit** for GPU services)
- **NVIDIA GPU + CUDA drivers** (required for `joycaption` and `kyutai-stt`)
- Optional: `curl`, `ffmpeg` for quick testing

---

## Directory Layout

```
services/
├─ joycaption/
│  └─ start.sh
├─ kitten-tts/
│  ├─ start.sh
│  └─ app.py               # FastAPI service (TTS)
├─ kyutai-stt/
│  └─ start.sh
└─ README.md               # this file
```

All services mount the local Hugging Face cache at `~/.cache/huggingface` into the container to avoid re-downloading models.

---

## Quick Start

```bash
# Joycaption (image captioning via vLLM)
cd joycaption && ./start.sh

# Kitten TTS (text-to-speech API)
cd kitten-tts && ./start.sh

# Kyutai STT (speech-to-text worker)
cd kyutai-stt && ./start.sh
```

**Default ports**
- joycaption → `http://127.0.0.1:7002`
- kitten-tts → `http://127.0.0.1:7003`
- kyutai-stt → configured by the worker config (see below)

---

## Services

### 1. joycaption

**Description**  
`joycaption` runs a multimodal LLaMA-based model for image captioning using **vLLM**’s OpenAI-compatible server. It uses GPU acceleration and mounts your Hugging Face cache.

**Start Script**
```bash
docker stop joy-caption
docker rm joy-caption

docker run   --name joy-caption   --gpus all   -p 127.0.0.1:7002:80   -v ~/.cache/huggingface:/root/.cache/huggingface   vllm/vllm-openai:v0.8.5.post1   --model fancyfeast/llama-joycaption-beta-one-hf-llava   --port 80   --gpu-memory-utilization 0.95   --max-model-len 4096   --enforce-eager   --limit-mm-per-prompt image=2
```

**Run**
```bash
cd joycaption
./start.sh
```

**Test with curl (OpenAI-compatible API)**  
Set an arbitrary API key (vLLM accepts any value by default):
```bash
export OPENAI_API_KEY=dummy
curl -s http://127.0.0.1:7002/v1/chat/completions   -H "Authorization: Bearer $OPENAI_API_KEY"   -H "Content-Type: application/json"   -d '{
    "model": "fancyfeast/llama-joycaption-beta-one-hf-llava",
    "messages": [{
      "role": "user",
      "content": [
        {"type":"text","text":"Caption this image briefly."},
        {"type":"image_url","image_url":{"url":"https://picsum.photos/seed/cat/512"}}
      ]
    }]
  }' | jq -r '.choices[0].message.content'
```

---

### 2. kitten-tts

**Description**  
`kitten-tts` provides a TTS API using FastAPI. It wraps `KittenTTS` and outputs **16‑bit PCM** at **24 kHz** (media type `audio/l16;rate=24000`).

**Start Script**
```bash
# start.sh
BASEDIR=$(dirname "$0")
echo "$BASEDIR"

docker stop kitten-tts
docker rm kitten-tts

docker build --tag kitten-tts:latest "$BASEDIR"

docker run   --name kitten-tts   -p 127.0.0.1:7003:80   -v ~/.cache/huggingface:/root/.cache/huggingface   kitten-tts:latest
```

**API**
- `POST /tts`
- Request body:
```json
{
  "text": "Hello world",
  "voice": "default"
}
```
- Response: raw PCM bytes (`audio/l16;rate=24000`, mono), little‑endian 16‑bit.

**Reference implementation (app.py)**
```python
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
    # Convert to 16-bit PCM (ensure even byte length)
    audio_int16 = (audio * 32767).astype(np.int16)
    audio_bytes = audio_int16.tobytes()
    if len(audio_bytes) % 2 != 0:
        audio_bytes += b"\x00"
    return Response(content=audio_bytes, media_type="audio/l16;rate=24000")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=80)
```

**Run**
```bash
cd kitten-tts
./start.sh
```

**Test with curl + ffmpeg (save as WAV)**
```bash
# Request TTS and save raw PCM
curl -s -X POST http://127.0.0.1:7003/tts   -H "Content-Type: application/json"   -d '{"text":"Hello from Gabber Kitten TTS","voice":"default"}' > out.pcm

# Convert raw PCM → WAV (mono, 16-bit, 24kHz)
ffmpeg -f s16le -ar 24000 -ac 1 -i out.pcm out.wav -y
# Play (macOS):
afplay out.wav
```

---

### 3. kyutai-stt

**Description**  
`kyutai-stt` runs a speech-to-text worker using **moshi-server**. It supports multi‑language transcription via a TOML config.

**Start Script**
```bash
#!/bin/bash
# Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
# SPDX-License-Identifier: SUL-1.0

set -e
echo "Starting unmute STT worker..."

export RUST_LOG=trace
export CUDA_LAUNCH_BLOCKING=1
export CUDA_LOG_LEVEL=5

moshi-server worker --config ~/delayed-streams-modeling/configs/config-stt-en_fr_hf.toml
```

**Run**
```bash
cd kyutai-stt
./start.sh
```

**Notes**
- Requires an NVIDIA GPU and CUDA drivers.
- Verbose logs (`trace`) are enabled for debugging.
- The worker consumes audio jobs from the configured queue/backplane per the TOML file.

---

## Development Notes

- **Hugging Face Cache**: Mounted at `~/.cache/huggingface:/root/.cache/huggingface` in the containers.
- **GPU Acceleration**: `joycaption` and `kyutai-stt` require NVIDIA GPUs with drivers + `nvidia-container-toolkit` installed.
- **Ports Recap**: `7002` (joycaption), `7003` (kitten-tts). Adjust in `start.sh` if needed.

---

## Troubleshooting

- **`nvidia-container-cli: initialization error`** → Install/configure NVIDIA drivers and `nvidia-container-toolkit`, then restart Docker.
- **Model repeatedly downloads** → Ensure the HF cache mount exists and is writable: `~/.cache/huggingface`.
- **TTS audio sounds clipped or wrong speed** → Verify conversion flags: `-f s16le -ar 24000 -ac 1` when using `ffmpeg`.
- **Port already in use** → Change the host port mapping in the `-p` flag of the relevant `start.sh`.

---

## License

Unless otherwise noted in a given folder, code and scripts are provided under **SUL-1.0**. See file headers for details.

