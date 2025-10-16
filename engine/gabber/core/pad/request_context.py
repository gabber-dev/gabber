# Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
# SPDX-License-Identifier: SUL-1.0

import asyncio
import logging
import time
from typing import Callable
from ..types import runtime

from gabber.utils import short_uuid


class RequestContext:
    def __init__(
        self,
        *,
        parent: "RequestContext | None",
        timeout: float = 30.0,
        originator: str | None = None,
    ) -> None:
        self.originator = originator
        self.results: list[runtime.RuntimePadValue] = []
        self.id = short_uuid()
        if parent is None:
            self.start_time = time.time()
            self._timeout_s = timeout
        else:
            self.start_time = parent.start_time
            self._timeout_s = parent._timeout_s

        self.parent = parent
        self.dependencies: list[RequestContext] = []
        parent.dependencies.append(self) if parent else None
        self._self_completed = False
        self._finished = False
        self._done_callbacks: list[Callable[[list[runtime.RuntimePadValue]], None]] = []
        o_req = self

        self.distance_to_root = 0
        while o_req.parent:
            self.distance_to_root += 1
            o_req = o_req.parent
        self._original_request = o_req

        if self.distance_to_root > 1000:
            raise RuntimeError(
                f"RequestContext {self} has exceeded maximum size of 1000. Do you have an infinite loop?"
            )

        RequestContextRegistry().register(self)

    def append_result(self, item: runtime.RuntimePadValue) -> None:
        self.results.append(item)

    def complete(self):
        if self._finished:
            return
        if self._self_completed:
            self._resolve_finished()
            return

        self._self_completed = True

        # If we don't have any done callbacks, we can
        # safely remove this request from the chain
        # This helps prune in loop situations
        if self.parent and len(self._done_callbacks) == 0:
            self.parent.dependencies.extend(self.dependencies)
            for dep in self.dependencies:
                dep.parent = self.parent
            self.dependencies = []

        self._resolve_finished()

    def timeout(self):
        logging.warning("RequestContext timed out.")
        self.complete()

    def _resolve_finished(self):
        for d in self.dependencies:
            if not d._finished:
                return

        self._finished = True
        for cb in self._done_callbacks:
            try:
                cb(self.results)
            except Exception as e:
                logging.error(f"Error in done callback: {e}")
        self._done_callbacks = []

        if self.parent:
            self.parent._resolve_finished()

    def add_done_callback(
        self, callback: Callable[[list[runtime.RuntimePadValue]], None]
    ) -> None:
        self._done_callbacks.append(callback)

    @property
    def original_request(self) -> "RequestContext":
        return self._original_request

    def find_parent_by_originator(self, originator: str) -> "RequestContext | None":
        if self.originator == originator:
            return self

        if self.parent:
            return self.parent.find_parent_by_originator(originator)

        return None

    def snooze_timeout(self, seconds: float) -> None:
        if self._finished:
            return
        self._timeout_s += seconds
        parent = self.parent
        while parent:
            parent._timeout_s += seconds
            parent = parent.parent


class RequestContextRegistry:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.initialize()
        return cls._instance

    def initialize(self):
        self._requests = set["RequestContext"]()
        self._timeout_task = asyncio.create_task(self._run())

    def register(self, request: "RequestContext") -> None:
        if len(self._requests) >= 100_000:
            logging.error(
                "RequestContextRegistry has reached maximum capacity of 100,000. "
            )
            request.complete()
            return
        self._requests.add(request)

    def get_all_requests(self) -> set["RequestContext"]:
        return self._requests

    def clear(self) -> None:
        self._requests.clear()
        logging.info("Cleared all registered RequestContexts")

    async def _run(self):
        while True:
            await asyncio.sleep(1)
            now = time.time()
            for request in list(self._requests):
                if request._finished:
                    self._requests.remove(request)
                    request.dependencies = []
                    request._done_callbacks = []
                else:
                    elapsed = now - request.start_time
                    if elapsed > request._timeout_s:
                        logging.warning(
                            f"RequestContext {request} timed out after {elapsed:.2f} seconds. Originator: {request.originator}"
                        )
                        request.timeout()
                        self._requests.remove(request)

            if len(self._requests) > 0:
                logging.debug("pending request count: %d", len(self._requests))
