import logging
import asyncio
import base64
import pyaudio
import uuid
import aiohttp
import threading

CHUNK = 441
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100

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
        self._loop = asyncio.get_event_loop()
        self._input_queue = asyncio.Queue[bytes | None](maxsize=10)
        self._connected = False

    def _stream_thread(self):
        while True:
            data = self._stream.read(CHUNK, exception_on_overflow=False)
            if not self._connected:
                continue
            self._loop.call_soon_threadsafe(self._input_queue.put_nowait, data)

    async def run(self):
        thread = threading.Thread(target=self._stream_thread)
        thread.start()

        async def send_task(ws: aiohttp.ClientWebSocketResponse, session_id: str):
            start_msg = self._start_session_message(session_id)
            await ws.send_json(start_msg)
            while True:
                data = await self._input_queue.get()
                if data is None:
                    break

                req = self._audio_request_message(session_id, data)
                await ws.send_json(req)

        async def recv_task(ws: aiohttp.ClientWebSocketResponse):
            async for msg in ws:
                if msg.type == aiohttp.WSMsgType.TEXT:
                    print(f"Received: {msg.data}")
                elif msg.type == aiohttp.WSMsgType.ERROR:
                    break

        while True:
            send_t: asyncio.Task | None = None
            recv_t: asyncio.Task | None = None
            try:
                async with aiohttp.ClientSession() as session:
                    session_id = str(uuid.uuid4())
                    async with session.ws_connect("ws://127.0.0.1:7004") as ws:
                        self._connected = True
                        logging.info("Connected to server")
                        send_t = asyncio.create_task(send_task(ws, session_id))
                        recv_t = asyncio.create_task(recv_task(ws))
                        await send_t
                        await recv_t
            except Exception as e:
                if send_t:
                    send_t.cancel()
                if recv_t:
                    recv_t.cancel()
                logging.error(f"Connection error: {e}")

            send_t = None
            recv_t = None
            logging.info("Reconnecting...")
            await asyncio.sleep(1)

    def _start_session_message(self, id):
        return {
            "session_id": id,
            "payload": {
                "type": "start_session",
                "sample_rate": RATE,
                "stt_enabled": True,
                "lipsync_enabled": False,
            },
        }

    def _audio_request_message(self, id: str, chunk: bytes):
        b64_chunk = base64.b64encode(chunk).decode("utf-8")
        return {
            "session_id": id,
            "payload": {
                "type": "audio",
                "b64_data": b64_chunk,
            },
        }

    def _end_session_message(self, id: str):
        return {
            "session_id": id,
            "payload": {
                "type": "end_session",
            },
        }


async def main():
    client = TestClient()
    await client.run()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
