# Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
# SPDX-License-Identifier: SUL-1.0

import asyncio
import json
import logging
import os
import sys
import time

from livekit import agents, rtc
from livekit.agents import cli

from gabber.core.editor import models
from gabber.core.graph import Graph, GraphLibrary
from gabber.core.graph.runtime_api import RuntimeApi
from gabber.core.secret import SecretProvider
from .default_graph_library import DefaultGraphLibrary
from .default_secret_provider import DefaultSecretProvider
from gabber.core.logger import GabberLogHandler


async def entrypoint(ctx: agents.JobContext):
    parsed = json.loads(ctx.job.metadata)
    graph_rep = parsed["graph"]
    graph_rep = models.GraphEditorRepresentation.model_validate(graph_rep)

    graph_library: GraphLibrary = DefaultGraphLibrary()
    secret_provider: SecretProvider = DefaultSecretProvider()

    os.environ["TZ"] = "UTC"
    time.tzset()

    library_items = await graph_library.list_items()
    secrets = await secret_provider.list_secrets()
    all_secrets = await asyncio.gather(
        *[secret_provider.resolve_secret(s) for s in secrets]
    )
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
    )
    log_handler_t = asyncio.create_task(log_handler.run())
    await graph.load_from_snapshot(graph_rep)
    await ctx.connect()
    room = ctx.room
    graph_t = asyncio.create_task(graph.run(room=room, runtime_api=runtime_api))

    async def track_participants_loop():
        while True:
            await asyncio.sleep(5)
            humans = [
                p
                for p in ctx.room.remote_participants.values()
                if p.kind == rtc.ParticipantKind.PARTICIPANT_KIND_STANDARD
            ]

            if len(humans) == 0:
                logging.info("No participants detected, starting shutdown timer.")
                # TODO make this configurable
                await asyncio.sleep(5)
                humans = [
                    p
                    for p in ctx.room.remote_participants.values()
                    if p.kind == rtc.ParticipantKind.PARTICIPANT_KIND_STANDARD
                ]
                if len(humans) == 0:
                    logging.info("No participants left, shutting down.")
                    await ctx.room.disconnect()
                    graph_t.cancel()
                    return

                logging.info("Participants rejoined, cancelling shutdown.")

    participant_track_task = asyncio.create_task(track_participants_loop())

    try:
        await graph_t
    except asyncio.CancelledError:
        logging.info("Job cancelled, shutting down gracefully.")
    except Exception as e:
        logging.error(f"An error occurred while running the graph: {e}", exc_info=True)

    try:
        await participant_track_task
    except Exception as e:
        logging.error(f"An error occurred in participant tracking: {e}", exc_info=True)

    log_handler.close()
    log_handler_t.cancel()

    try:
        await log_handler_t
    except asyncio.CancelledError:
        pass


def cpu_load_fnc(worker: agents.Worker) -> float:
    return float(len(worker.active_jobs)) / 4


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
