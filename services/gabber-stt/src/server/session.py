import asyncio
import logging

from .messages import (
    Request,
    RequestPayload,
    RequestPayload_AudioData,
    RequestPayload_EndSession,
    Response,
    ResponsePayload,
    ResponsePayload_Error,
    ResponsePayload_Transcription,
)
from engine import Engine
from typing import Callable

logger = logging.getLogger(__name__)


class SessionManager:
    def __init__(self, *, engine_factory: Callable[[], Engine]):
        self._request_queue = []
        self._engine_factory = engine_factory

        self._session_lookup: dict[str, Session] = {}
        self._session_run_tasks: dict[str, asyncio.Task] = {}
        self._session_send_tasks: dict[str, asyncio.Task] = {}
        self._output_queue: asyncio.Queue[Response | None] = asyncio.Queue()

    def push_request(self, request: Request):
        if request.payload.type == "start_session":
            sess_id = request.session_id
            if sess_id in self._session_lookup:
                logger.error(f"Session {sess_id} already exists")
                return

            output_queue: asyncio.Queue[ResponsePayload | Exception | None] = (
                asyncio.Queue()
            )
            session = Session(
                id=sess_id,
                engine=self._engine_factory(),
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
        self._engine = engine
        self._req_q: asyncio.Queue[RequestPayload | None] = asyncio.Queue(maxsize=100)
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

    async def run(self):
        while True:
            req = await self._req_q.get()
            if req is None:
                break

            if isinstance(req, RequestPayload_AudioData):
                self.logger.info(f"Received audio data of size {len(req.b64_data)}")
                payload = ResponsePayload_Transcription(
                    start_sample=0,
                    end_sample=16000,
                    words=[],
                    transcription="simulated transcription",
                )
                await self._output_queue.put(payload)
            elif isinstance(req, RequestPayload_EndSession):
                self.logger.info("Received end session request")
                break
