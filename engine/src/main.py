# Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
# SPDX-License-Identifier: SUL-1.0

import asyncio
import json
import logging

import click
from core.editor import messages
from pydantic import TypeAdapter
from server import (
    GraphEditorServer,
    run_engine,
    repository,
    DefaultGraphLibrary,
    DefaultSecretProvider,
)


@click.group()
def main_cli():
    logging.basicConfig(level=logging.INFO)


@main_cli.command("editor")
@click.option("--port", default=8000, help="Port to run the server on")
def start(port):
    """Start the graph editor server"""

    async def run_server():
        server = GraphEditorServer(
            port=port,
            graph_library=DefaultGraphLibrary(),
            secret_provider=DefaultSecretProvider(),
        )
        await server.run()

    asyncio.run(run_server())


@main_cli.command("engine")
@click.pass_context
def engine(ctx: click.Context):
    """Start the engine"""
    run_engine(
        livekit_api_key="devkey",
        livekit_api_secret="secret",
        livekit_url="ws://localhost:7880",
    )


@main_cli.command("repository")
def repository_server():
    """Start the repository server"""

    async def run_repository():
        server = repository.RepositoryServer(port=8001)
        await server.run()

    asyncio.run(run_repository())


@main_cli.command("generate-editor-schema")
def generate_editor_schema():
    """Generate merged JSON schema for TypeScript generation"""

    request_adapter = TypeAdapter(messages.Request)
    request_schema = request_adapter.json_schema()
    response_schema = messages.Response.model_json_schema()

    # Merge schemas at root level
    merged_schema = {
        "$defs": {},
        "oneOf": [{"$ref": "#/$defs/Request"}, {"$ref": "#/$defs/Response"}],
    }

    # Add all definitions from both schemas
    if "$defs" in request_schema:
        merged_schema["$defs"].update(request_schema["$defs"])
    if "definitions" in request_schema:
        merged_schema["$defs"].update(request_schema["definitions"])

    if "$defs" in response_schema:
        merged_schema["$defs"].update(response_schema["$defs"])
    if "definitions" in response_schema:
        merged_schema["$defs"].update(response_schema["definitions"])

    # Add the root schemas as definitions
    request_root = {
        k: v for k, v in request_schema.items() if k not in ["$defs", "definitions"]
    }
    response_root = {
        k: v for k, v in response_schema.items() if k not in ["$defs", "definitions"]
    }

    merged_schema["$defs"]["Request"] = request_root
    merged_schema["$defs"]["Response"] = response_root

    # Convert $defs to definitions for older tools if needed
    if merged_schema["$defs"]:
        merged_schema["definitions"] = merged_schema.pop("$defs")
        # Update all $ref pointers
        schema_str = json.dumps(merged_schema)
        schema_str = schema_str.replace("#/$defs/", "#/definitions/")
        merged_schema = json.loads(schema_str)

    print(json.dumps(merged_schema, indent=2))


@main_cli.command("generate-repository-schema")
def generate_repository_schema():
    """Generate merged JSON schema for TypeScript generation"""

    request_adapter = TypeAdapter(repository.messages.Request)
    request_schema = request_adapter.json_schema()
    response_adapter = TypeAdapter(repository.messages.Response)
    response_schema = response_adapter.json_schema()

    # Merge schemas at root level
    merged_schema = {
        "$defs": {},
        "oneOf": [{"$ref": "#/$defs/Request"}, {"$ref": "#/$defs/Response"}],
    }

    # Add all definitions from both schemas
    if "$defs" in request_schema:
        merged_schema["$defs"].update(request_schema["$defs"])
    if "definitions" in request_schema:
        merged_schema["$defs"].update(request_schema["definitions"])

    if "$defs" in response_schema:
        merged_schema["$defs"].update(response_schema["$defs"])
    if "definitions" in response_schema:
        merged_schema["$defs"].update(response_schema["definitions"])

    # Add the root schemas as definitions
    request_root = {
        k: v for k, v in request_schema.items() if k not in ["$defs", "definitions"]
    }
    response_root = {
        k: v for k, v in response_schema.items() if k not in ["$defs", "definitions"]
    }

    merged_schema["$defs"]["Request"] = request_root
    merged_schema["$defs"]["Response"] = response_root

    # Convert $defs to definitions for older tools if needed
    if merged_schema["$defs"]:
        merged_schema["definitions"] = merged_schema.pop("$defs")
        # Update all $ref pointers
        schema_str = json.dumps(merged_schema)
        schema_str = schema_str.replace("#/$defs/", "#/definitions/")
        merged_schema = json.loads(schema_str)

    print(json.dumps(merged_schema, indent=2))


if __name__ == "__main__":
    main_cli()
