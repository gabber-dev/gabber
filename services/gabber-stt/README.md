# Gabber Streaming STT Service

Incorporates the following models into a streaming STT websocket service with end-of-turn detection:
- Parakeet for ASR
- Silero for VAD
- Pipecat for EOT

Start a test session:
```bash
make all
```

Start the server:
```bash
make server
```