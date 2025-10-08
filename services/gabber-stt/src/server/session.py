import asyncio
import logging
import base64

from .messages import (
    Request,
    RequestPayload,
    RequestPayload_AudioData,
    RequestPayload_StartSession,
    RequestPayload_EndSession,
    Response,
    ResponsePayload,
    ResponsePayload_Error,
    engine_event_to_response_payload,
)
from engine import Engine, EngineEvent
from typing import Callable

logger = logging.getLogger(__name__)


class SessionManager:
    def __init__(
        self, *, engine_factory: Callable[[RequestPayload_StartSession], Engine]
    ):
        self._request_queue = []
        self._engine_factory = engine_factory

        self._session_lookup: dict[str, Session] = {}
        self._session_run_tasks: dict[str, asyncio.Task] = {}
        self._session_send_tasks: dict[str, asyncio.Task] = {}
        self._output_queue: asyncio.Queue[Response | None] = asyncio.Queue()

    def push_request(self, request: Request):
        if request.payload.type == "start_session":
            logger.info(f"Starting session {request.session_id}")
            sess_id = request.session_id
            if sess_id in self._session_lookup:
                logger.error(f"Session {sess_id} already exists")
                return

            output_queue: asyncio.Queue[ResponsePayload | Exception | None] = (
                asyncio.Queue()
            )
            eng = self._engine_factory(request.payload)
            session = Session(
                id=sess_id,
                engine=eng,
                output_queue=output_queue,
            )
            session_t = asyncio.create_task(session.run())
            session_send_t = asyncio.create_task(
                self._session_send_task(id=sess_id, output_queue=output_queue)
            )
            self._session_lookup[sess_id] = session
            self._session_run_tasks[sess_id] = session_t
            self._session_send_tasks[sess_id] = session_send_t

            session_t.add_done_callback(
                lambda _: self._session_run_tasks.pop(sess_id, None)
            )
            session_t.add_done_callback(
                lambda _: self._session_send_tasks.pop(sess_id, None)
            )
            session_send_t.add_done_callback(
                lambda _: self._session_send_tasks.pop(sess_id, None)
            )
            return

        sess_id = request.session_id
        session = self._session_lookup.get(sess_id, None)
        if session is None:
            logger.error(f"Session {sess_id} does not exist")
            return

        session.push_payload(request.payload)

    async def _session_send_task(
        self,
        *,
        id: str,
        output_queue: asyncio.Queue[ResponsePayload | Exception | None],
    ):
        while True:
            payload = await output_queue.get()
            if isinstance(payload, Exception):
                response = Response(
                    session_id=id,
                    payload=ResponsePayload_Error(message=str(payload)),
                )
                self._output_queue.put_nowait(response)
                break

            if payload is None:
                break

            response = Response(session_id=id, payload=payload)
            self._output_queue.put_nowait(response)

        session_run_t = self._session_run_tasks.get(id, None)
        if session_run_t:
            session_run_t.cancel()

    def __aiter__(self):
        return self

    async def __anext__(self) -> Response:
        response = await self._output_queue.get()
        if response is None:
            raise StopAsyncIteration
        return response


class Session:
    def __init__(
        self,
        *,
        id: str,
        engine: Engine,
        output_queue: asyncio.Queue[ResponsePayload | Exception | None],
    ):
        engine.set_event_handler(self.engine_event)
        self._engine = engine
        self._req_q: asyncio.Queue[RequestPayload | None] = asyncio.Queue(maxsize=1024)
        self.logger = logging.LoggerAdapter(logger, {"session_id": id})
        self._output_queue = output_queue
        self._closed = False

    def push_payload(self, request: RequestPayload):
        if self._closed:
            self.logger.warning("Session closed, ignoring message")

        try:
            self._req_q.put_nowait(request)
        except asyncio.QueueFull:
            self.logger.error("Session queue full")
            self._output_queue.put_nowait(Exception("Session Queue full"))

    def eos(self):
        self._closed = True
        self._req_q.put_nowait(None)

    def engine_event(self, evt: EngineEvent):
        payload = engine_event_to_response_payload(evt)
        self._output_queue.put_nowait(payload)

    async def run(self):
        engine_t = asyncio.create_task(self._engine.run())
        while True:
            req = await self._req_q.get()
            if req is None:
                break

            if engine_t.done():
                break

            if isinstance(req, RequestPayload_AudioData):
                audio_bytes = base64.b64decode(req.b64_data)
                self._engine.push_audio(audio_bytes)
            elif isinstance(req, RequestPayload_EndSession):
                self.logger.info("Received end session request")
                break

        try:
            await engine_t
        except asyncio.CancelledError:
            pass
        except Exception as e:
            self.logger.error(f"Engine error: {e}")
            self._output_queue.put_nowait(e)
