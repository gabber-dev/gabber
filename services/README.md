# Gabber Services

Small helper services used by some nodes. Each folder has a `start.sh` that builds and runs a container.

## Quickstart

```bash
# TTS (kitten-tts) → serves audio/l16;rate=24000 on :7003
cd kitten-tts && ./start.sh

# STT worker (kyutai-stt) → requires NVIDIA GPU/CUDA
cd kyutai-stt && ./start.sh
```

## Notes

- `kitten-tts` maps `127.0.0.1:7003 -> container:80`
- `kyutai-stt` uses your local worker config; see its `start.sh`
- For engine usage, see the top‑level README: ../README.md

## Troubleshooting

- Port in use → change the `-p` mapping in `start.sh`
- GPU errors → install NVIDIA drivers + `nvidia-container-toolkit`

