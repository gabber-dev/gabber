from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import json

app = FastAPI(
    title="PCM Audio WebSocket Server",
    description="A simple FastAPI WebSocket server that accepts streaming PCM audio",
)


@app.websocket("/ws/audio")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for streaming PCM audio data.
    Expects binary messages with raw PCM audio bytes (e.g., 16-bit, mono, 16kHz sample rate).
    Accumulates received data and responds with JSON status updates.
    """
    await websocket.accept()
    accumulated_size = 0
    try:
        while True:
            # Receive binary data (PCM audio chunk)
            data = await websocket.receive_bytes()
            chunk_size = len(data)
            accumulated_size += chunk_size

            # Optional: Basic validation
            if chunk_size == 0:
                await websocket.send_text(json.dumps({"error": "Empty chunk received"}))
                continue

            # Here you can process the PCM data further, e.g., analyze, save, or stream to another service
            # For example, using numpy: import numpy as np; audio_chunk = np.frombuffer(data, dtype=np.int16)

            # Send acknowledgment
            response = {
                "message": "PCM chunk received successfully",
                "chunk_size_bytes": chunk_size,
                "total_accumulated_bytes": accumulated_size,
                "sample_rate_hint": "Assume 16kHz (customize as needed)",
            }
            await websocket.send_text(json.dumps(response))

    except WebSocketDisconnect:
        print("Client disconnected")
    except Exception as e:
        await websocket.send_text(json.dumps({"error": str(e)}))
    finally:
        print(f"Session ended. Total audio bytes: {accumulated_size}")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
