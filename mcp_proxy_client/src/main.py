# Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
# SPDX-License-Identifier: SUL-1.0

import asyncio
import logging
from typing import Literal

import click

from app import App
from connection import LocalConnectionProvider, ConnectionProvider


@click.group()
def main_cli():
    logging.basicConfig(level=logging.INFO)


@main_cli.command("start")
@click.option("--backend", type=click.Choice(["local", "cloud"]), default="local")
@click.argument("run_id")
def start(backend: Literal["local", "cloud"], run_id: str):
    async def run_server():
        """Start the graph editor server"""
        conn_provider: ConnectionProvider
        if backend == "local":
            conn_provider = LocalConnectionProvider()
        elif backend == "cloud":
            raise NotImplementedError("Cloud backend coming soon!")

        p = App(connection_provider=conn_provider, run_id=run_id)
        try:
            await p.run()
        except Exception as e:
            logging.error(f"Error occurred while running server: {e}", exc_info=True)

    asyncio.run(run_server())


if __name__ == "__main__":
    main_cli()
