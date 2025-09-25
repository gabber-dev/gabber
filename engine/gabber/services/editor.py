# Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
# SPDX-License-Identifier: SUL-1.0

import asyncio
import logging

import aiohttp
import aiohttp.web
from aiohttp import web
from pydantic import TypeAdapter

from gabber.core import graph, secret
from gabber.core.editor import messages
from typing import Callable


class GraphEditorServer:
    def __init__(
        self,
        *,
        port: int,
        graph_library_provider: Callable[[dict[str, str]], graph.GraphLibrary],
        secret_provider_provider: Callable[[dict[str, str]], secret.SecretProvider],
        logger: logging.Logger | logging.LoggerAdapter,
    ):
        self.port = port
        self.graph_library_provider = graph_library_provider
        self.secret_provider_provider = secret_provider_provider
        self.app = web.Application()
        self.logger = logger

        self.setup_routes()

    def setup_routes(self):
        self.app.router.add_get("/ws", self.websocket_handler)

    async def websocket_handler(self, request: aiohttp.web.Request):
        ws = web.WebSocketResponse()
        await ws.prepare(request)

        query_dict: dict[str, str] = dict(request.query)
        graph_library = self.graph_library_provider(query_dict)
        secret_provider = self.secret_provider_provider(query_dict)

        project = query_dict.get("project", "NONE")
        logger = logging.LoggerAdapter(self.logger, {"project": project})

        editor_session = GraphEditorSession(
            ws=ws,
            graph_library=graph_library,
            secret_provider=secret_provider,
            logger=logger,
        )
        await editor_session.run()

        return ws

    async def run(self):
        runner = web.AppRunner(self.app)
        await runner.setup()
        site = web.TCPSite(runner, ("0.0.0.0", "::"), self.port)
        print(f"Starting editor server on [::]:{self.port}")
        await site.start()

        # Keep the server running
        try:
            while True:
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            logging.info("Editor server has been cancelled.")
        except Exception as e:
            logging.error(f"Error in editor server: {e}", exc_info=True)

        try:
            await runner.cleanup()
        except Exception as e:
            logging.error(f"Error during editor server cleanup: {e}", exc_info=True)

        logging.info("Editor server has been shut down.")


class GraphEditorSession:
    def __init__(
        self,
        *,
        ws: web.WebSocketResponse,
        graph_library: graph.GraphLibrary,
        secret_provider: secret.SecretProvider,
        logger: logging.Logger | logging.LoggerAdapter,
    ):
        self.ws = ws
        self.graph_library = graph_library
        self.secret_provider = secret_provider
        self.logger = logger

    async def run(self):
        library_items = await self.graph_library.list_items()
        secrets = await self.secret_provider.list_secrets()
        self.graph = graph.Graph(
            secrets=secrets,
            secret_provider=self.secret_provider,
            library_items=library_items,
            logger=self.logger,
        )
        async for message in self.ws:
            if message.type == aiohttp.WSMsgType.TEXT:
                try:
                    adapter = TypeAdapter(messages.Request)
                    request = adapter.validate_json(message.data)
                    await self.handle_message(request)
                except Exception as e:
                    self.logger.error(f"Error handling message: {e}", exc_info=True)
                    # Optionally send error back to client
                    await self.ws.send_str(f"Error: {str(e)}")
            elif message.type == aiohttp.WSMsgType.ERROR:
                self.logger.error(f"WebSocket error: {self.ws.exception()}")
                break
            elif message.type == aiohttp.WSMsgType.CLOSE:
                self.logger.info("WebSocket connection closed")
                break

    async def handle_message(self, message: messages.Request):
        # Make this async if graph.handle_request needs to be async
        response = await self.graph.handle_request(message)

        # If you need to send a response back to the client
        if response:
            await self.ws.send_str(response.model_dump_json(serialize_as_any=True))
