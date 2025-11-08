# Gabber Streaming STT Service

This is a full streaming ASR service with batched inference, end-of-turn state-machine, and interim/final transcriptions.
It also implements a streaming viseme inference service for lipsync with 3D avatars.

Incorporates the following models into a streaming STT websocket service with end-of-turn detection:
- Parakeet for ASR
- Silero for VAD
- Pipecat for EOT
- OpenLipSync for visemes

See `src/server/messages.py` for websocket API interface.


Start a test session:
```bash
make all
```

Start the server:
```bash
make server
```