# Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
# SPDX-License-Identifier: SUL-1.0

import asyncio
import json
import logging
import os
import sys
import time
import gzip
import base64

from livekit import agents
from livekit.agents import cli

from gabber.core.editor import models
from gabber.core.graph import Graph, GraphLibrary
from gabber.core.graph.runtime_api import RuntimeApi
from gabber.core.secret import SecretProvider
from .default_graph_library import DefaultGraphLibrary
from .default_secret_provider import DefaultSecretProvider
from gabber.core.logger import GabberLogHandler
from typing import Any


async def entrypoint_inner(
    ctx: agents.JobContext,
    graph_library: GraphLibrary,
    secret_provider: SecretProvider,
    extra_secrets_to_omit: list[str] = [],
    extra: dict[str, Any] = {},
):
    md_str = ctx.job.metadata
    try:
        b64_decoded = base64.b64decode(ctx.job.metadata)
        if b64_decoded.startswith(b"\x1f\x8b"):
            gzipped_bytes = base64.b64decode(md_str)
            md_str = gzip.decompress(gzipped_bytes).decode("utf-8")
    except Exception:
        pass

    parsed = json.loads(md_str)
    graph_rep = parsed["graph"]
    graph_rep = models.GraphEditorRepresentation.model_validate(graph_rep)

    os.environ["TZ"] = "UTC"
    time.tzset()

    library_items = await graph_library.list_items()
    secrets = await secret_provider.list_secrets()
    all_secrets = await asyncio.gather(
        *[secret_provider.resolve_secret(s.id) for s in secrets]
    )
    all_secrets.extend(extra_secrets_to_omit)
    runtime_api = RuntimeApi(room=ctx.room)
    log_handler = GabberLogHandler(
        runtime_api=runtime_api, secrets_to_remove=all_secrets
    )
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    logger.addHandler(log_handler)
    logger.propagate = False

    graph = Graph(
        secrets=secrets,
        secret_provider=secret_provider,
        library_items=library_items,
        logger=logger,
        extra=extra,
    )
    log_handler_t = asyncio.create_task(log_handler.run())
    await graph.load_from_snapshot(graph_rep)
    await ctx.connect()
    room = ctx.room
    graph_t: asyncio.Task | None = asyncio.create_task(
        graph.run(room=room, runtime_api=runtime_api)
    )

    try:
        await graph_t
    except Exception as e:
        logger.error(f"Graph execution failed: {str(e)}")
    finally:
        logger.info("Graph task completed.")
        log_handler.close()
        log_handler_t.cancel()

        try:
            await log_handler_t
        except asyncio.CancelledError:
            pass


async def entrypoint(ctx: agents.JobContext):
    graph_library: GraphLibrary = DefaultGraphLibrary()
    secret_provider: SecretProvider = DefaultSecretProvider()
    await entrypoint_inner(ctx, graph_library, secret_provider)


def cpu_load_fnc(worker: agents.Worker) -> float:
    return float(len(worker.active_jobs)) / 8


async def req_fnc(worker: agents.JobRequest):
    await worker.accept(name="gabber-engine", identity="gabber-engine")


def run_engine(
    *,
    livekit_api_key: str,
    livekit_api_secret: str,
    livekit_url: str,
):
    os.environ["LIVEKIT_API_KEY"] = livekit_api_key
    os.environ["LIVEKIT_API_SECRET"] = livekit_api_secret
    os.environ["LIVEKIT_URL"] = livekit_url

    original_argv = sys.argv[:]
    sys.argv = [sys.argv[0], "dev"]
    cli.run_app(
        agents.WorkerOptions(
            request_fnc=req_fnc,
            agent_name="gabber-engine",
            load_fnc=cpu_load_fnc,
            load_threshold=0.99,
            entrypoint_fnc=entrypoint,
            num_idle_processes=1,
            shutdown_process_timeout=60,
        )
    )
    sys.argv = original_argv
