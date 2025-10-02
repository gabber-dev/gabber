import asyncio
import json
import logging

from aiohttp import web

from .messages import Request, RequestPayload_StartSession
from .session import SessionManager
from engine import Engine
from typing import Callable


class WebSocketServer:
    def __init__(
        self, *, engine_factory: Callable[[RequestPayload_StartSession], Engine]
    ):
        self.engine_factory = engine_factory
        self.app = web.Application()
        self.app.router.add_get("/", self.endpoint)

    async def endpoint(self, request):
        ws = web.WebSocketResponse()
        await ws.prepare(request)
        try:
            await self.handle(ws)
        finally:
            await ws.close()
        return ws

    async def handle(self, ws: web.WebSocketResponse):
        session_manager = SessionManager(engine_factory=self.engine_factory)

        async def send_task():
            async for message in session_manager:
                await ws.send_str(json.dumps(message))

        async def recv_task():
            try:
                while True:
                    data = await ws.receive_json()
                    request: Request
                    try:
                        request = Request.model_validate(data)
                        session_manager.push_request(request)
                    except Exception as e:
                        logging.error(f"Failed to parse request: {e}")
                        continue

            except Exception as e:
                await ws.send_str(json.dumps({"error": str(e)}))

        send_t = asyncio.create_task(send_task())
        recv_t = asyncio.create_task(recv_task())

        try:
            await asyncio.gather(send_t, recv_t)
        except Exception as e:
            logging.error(f"WebSocket error: {e}")

        send_t.cancel()
        recv_t.cancel()

        try:
            await send_t
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logging.error(f"Send task error: {e}")

        try:
            await recv_t
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logging.error(f"Receive task error: {e}")

        await ws.close()

    def run(self, host="0.0.0.0", port=8000):
        web.run_app(self.app, host=host, port=port)
