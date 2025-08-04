# Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
# SPDX-License-Identifier: SUL-1.0

import asyncio
import json
import logging
import os
import sys
import time

from livekit import agents 
from livekit.agents import cli

from core.editor import models
from core.graph import Graph, GraphLibrary
from core.secret import SecretProvider
from .default_graph_library import DefaultGraphLibrary
from .default_secret_provider import DefaultSecretProvider


async def entrypoint(ctx: agents.JobContext):
    global _graph_library, _secret_provider
    parsed = json.loads(ctx.job.metadata)
    graph_rep = parsed["graph"]
    graph_rep = models.GraphEditorRepresentation.model_validate(graph_rep)

    graph_library: GraphLibrary = DefaultGraphLibrary()
    secret_provider: SecretProvider = DefaultSecretProvider()

    os.environ["TZ"] = "UTC"
    time.tzset()

    library_items = await graph_library.list_items()
    secrets = await secret_provider.list_secrets()
    graph = Graph(
        secrets=secrets,
        secret_provider=secret_provider,
        library_items=library_items,
    )
    await graph.load_from_snapshot(graph_rep)

    await ctx.connect()
    room = ctx.room

    try:
        await graph.run(room=room)
    except asyncio.CancelledError:
        logging.info("Job cancelled, shutting down gracefully.")
    except Exception as e:
        logging.error(f"An error occurred while running the graph: {e}", exc_info=True)


def cpu_load_fnc(worker: agents.Worker) -> float:
    return float(len(worker.active_jobs)) / 4


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
            agent_name="gabber-engine",
            load_fnc=cpu_load_fnc,
            load_threshold=0.99,
            entrypoint_fnc=entrypoint,
            num_idle_processes=1,
            shutdown_process_timeout=60,
        )
    )
    sys.argv = original_argv
