# Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
# SPDX-License-Identifier: SUL-1.0

import asyncio
import datetime
import json
import logging
import os
from uuid import uuid4

import aiofiles
import aiohttp
import aiohttp.web
import aiohttp_cors
from aiohttp import web
from livekit import api
from gabber.utils import short_uuid

from gabber.core.editor.models import GraphEditorRepresentation

from . import messages, models


class RepositoryServer:
    def __init__(self, port: int):
        file_path = os.environ["GABBER_REPOSITORY_DIR"]
        self.file_path = file_path
        self.port = port
        self.app = web.Application()
        self.setup_routes()
        cors = aiohttp_cors.setup(
            self.app,
            defaults={
                "*": aiohttp_cors.ResourceOptions(
                    allow_credentials=True,
                    expose_headers="*",
                    allow_headers="*",
                    allow_methods="*",
                )
            },
        )
        for route in list(self.app.router.routes()):
            cors.add(route)

    def setup_routes(self):
        self.app.router.add_get("/app/list", self.list_apps)
        self.app.router.add_post("/app", self.save_app)
        self.app.router.add_get("/app/{id}", self.get_app)
        self.app.router.add_delete("/app/{id}", self.delete_app)
        self.app.router.add_get("/sub_graph/list", self.list_subgraphs)
        self.app.router.add_post("/sub_graph", self.save_subgraph)
        self.app.router.add_get("/sub_graph/{id}", self.get_subgraph)
        self.app.router.add_delete("/sub_graph/{id}", self.delete_subgraph)
        self.app.router.add_get("/example/{id}", self.get_example)
        self.app.router.add_get("/example/list", self.list_examples)
        self.app.router.add_get("/premade_subgraph/{id}", self.get_premade_subgraph)
        self.app.router.add_get("/premade_subgraph/list", self.list_premade_subgraphs)
        self.app.router.add_post("/app/run", self.app_run)
        self.app.router.add_post("/app/debug_connection", self.debug_connection)
        self.app.router.add_post("/app/mcp_proxy_connection", self.mcp_proxy_connection)
        self.app.router.add_post("/app/import", self.import_app)
        self.app.router.add_get("/app/{id}/export", self.export_app)

    async def ensure_dir(self, dir_path: str):
        await asyncio.to_thread(os.makedirs, dir_path, exist_ok=True)

    async def get_app(self, request: aiohttp.web.Request):
        app_id = request.match_info.get("id")
        if not app_id:
            return aiohttp.web.json_response(
                {"status": "error", "message": "Missing app ID"}, status=400
            )

        try:
            async with aiofiles.open(
                f"{self.file_path}/app/{app_id}.json", mode="r"
            ) as json_file:
                json_content = await json_file.read()
            obj = models.RepositoryApp.model_validate_json(json_content)
            resp = messages.GetAppResponse(app=obj)
            return aiohttp.web.Response(
                body=resp.model_dump_json(), content_type="application/json"
            )
        except FileNotFoundError:
            return aiohttp.web.json_response(
                {"status": "error", "message": "App not found"}, status=404
            )

    async def list_apps(self, request: aiohttp.web.Request):
        try:
            app_dir = f"{self.file_path}/app"
            try:
                files = await asyncio.to_thread(os.listdir, app_dir)
            except FileNotFoundError:
                await self.ensure_dir(app_dir)
                files = []
            apps = []
            for file in files:
                if file.endswith(".json"):
                    async with aiofiles.open(
                        f"{self.file_path}/app/{file}", mode="r"
                    ) as f:
                        content = await f.read()
                        app = models.RepositoryApp.model_validate_json(content)
                        apps.append(app)
            sorted_by_created_at = sorted(
                apps, key=lambda x: x.created_at, reverse=True
            )
            response = messages.ListAppsResponse(apps=sorted_by_created_at)
            return aiohttp.web.Response(
                body=response.model_dump_json(), content_type="application/json"
            )
        except Exception as e:
            logging.error(f"Error listing apps: {e}")
            return aiohttp.web.json_response(
                {"status": "error", "message": str(e)}, status=500
            )

    async def save_app(self, request: aiohttp.web.Request):
        try:
            data = await request.json()
            req = messages.SaveAppRequest.model_validate(data)
            app: models.RepositoryApp | None = None
            if req.id:
                try:
                    async with aiofiles.open(
                        f"{self.file_path}/app/{req.id}.json", mode="r"
                    ) as f:
                        content = await f.read()
                        app = models.RepositoryApp.model_validate_json(content)
                except FileNotFoundError:
                    pass
            else:
                req.id = str(uuid4())
                app = models.RepositoryApp(
                    id=req.id,
                    name=req.name,
                    created_at=datetime.datetime.now(),
                    updated_at=datetime.datetime.now(),
                    graph=req.graph,
                )

            if not app:
                return aiohttp.web.json_response(
                    {"status": "error", "message": "App not found"}, status=404
                )

            app.updated_at = datetime.datetime.now()
            app.name = req.name
            app.graph = req.graph
            save_path = f"{self.file_path}/app/{req.id}.json"

            await self.ensure_dir(f"{self.file_path}/app")
            async with aiofiles.open(save_path, mode="w") as f:
                await f.write(app.model_dump_json())
            response = messages.SaveAppResponse(
                app=models.RepositoryApp.model_validate(app)
            )
            return aiohttp.web.Response(
                body=response.model_dump_json(), content_type="application/json"
            )
        except Exception as e:
            logging.error(f"Error saving app: {e}", exc_info=True)
            return aiohttp.web.json_response(
                {"status": "error", "message": str(e)}, status=400
            )

    async def delete_app(self, request: aiohttp.web.Request):
        app_id = request.match_info.get("id")
        if not app_id:
            return aiohttp.web.json_response(
                {"status": "error", "message": "Missing app ID"}, status=400
            )
        try:
            file_path = f"{self.file_path}/app/{app_id}.json"
            await asyncio.to_thread(os.remove, file_path)
            return aiohttp.web.json_response({"status": "success", "id": app_id})
        except FileNotFoundError:
            return aiohttp.web.json_response(
                {"status": "error", "message": "App not found"}, status=404
            )
        except Exception as e:
            logging.error(f"Error deleting app: {e}")
            return aiohttp.web.json_response(
                {"status": "error", "message": str(e)}, status=500
            )

    async def import_app(self, request: aiohttp.web.Request):
        try:
            data = await request.json()
            export = models.AppExport.model_validate(data)
            sub_graph_dir = f"{self.file_path}/sub_graph"
            mapping: dict[str, str] = {}
            for sg in export.subgraphs:
                original_id = sg.id
                new_id = original_id
                while True:
                    try:
                        await asyncio.to_thread(
                            os.stat, f"{sub_graph_dir}/{new_id}.json"
                        )
                        new_id += " duplicate"
                    except FileNotFoundError:
                        break
                existing_names = set()
                try:
                    files = await asyncio.to_thread(os.listdir, sub_graph_dir)
                except FileNotFoundError:
                    await self.ensure_dir(sub_graph_dir)
                    files = []
                for file in files:
                    if file.endswith(".json") and file[:-5] != new_id:
                        async with aiofiles.open(f"{sub_graph_dir}/{file}", "r") as f:
                            content = await f.read()
                            existing_sg = models.RepositorySubGraph.model_validate_json(
                                content
                            )
                            existing_names.add(existing_sg.name)
                name = sg.name
                while name in existing_names:
                    name += " duplicate"
                sg.id = new_id
                sg.name = name
                sg.created_at = datetime.datetime.now()
                sg.updated_at = datetime.datetime.now()
                save_path = f"{sub_graph_dir}/{sg.id}.json"
                await self.ensure_dir(sub_graph_dir)
                async with aiofiles.open(save_path, "w") as f:
                    await f.write(sg.model_dump_json())
                if original_id != new_id:
                    mapping[original_id] = new_id
            app = export.app
            app_dir = f"{self.file_path}/app"
            original_app_id = app.id
            new_app_id = original_app_id
            while True:
                try:
                    await asyncio.to_thread(os.stat, f"{app_dir}/{new_app_id}.json")
                    new_app_id += " duplicate"
                except FileNotFoundError:
                    break
            existing_names = set()
            try:
                files = await asyncio.to_thread(os.listdir, app_dir)
            except FileNotFoundError:
                await self.ensure_dir(app_dir)
                files = []
            for file in files:
                if file.endswith(".json"):
                    async with aiofiles.open(f"{app_dir}/{file}", "r") as f:
                        content = await f.read()
                        existing_app = models.RepositoryApp.model_validate_json(content)
                        existing_names.add(existing_app.name)
            name = app.name
            while name in existing_names:
                name += " duplicate"
            app.id = new_app_id
            app.name = name
            app.created_at = datetime.datetime.now()
            app.updated_at = datetime.datetime.now()
            if mapping:
                graph_json = app.graph.model_dump_json()
                for old, new in mapping.items():
                    graph_json = graph_json.replace(f'"{old}"', f'"{new}"')
                graph_dict = json.loads(graph_json)
                app.graph = GraphEditorRepresentation.model_validate(graph_dict)
            save_path = f"{app_dir}/{app.id}.json"
            await self.ensure_dir(app_dir)
            async with aiofiles.open(save_path, "w") as f:
                await f.write(app.model_dump_json())

            # Check for missing premade subgraphs
            def extract_subgraph_ids(graph: GraphEditorRepresentation) -> set[str]:
                ids = set()
                for node in graph.nodes:
                    if node.type != "SubGraph":
                        continue

                    id_pads = [p for p in node.pads if p.id == "__subgraph_id__"]
                    if len(id_pads) == 0:
                        raise ValueError("No __subgraph_id__ pad found")

                    if len(id_pads) > 1:
                        raise ValueError("Multiple __subgraph_id__ pads found")

                    val = id_pads[0].value
                    if not val:
                        raise ValueError("__subgraph_id__ pad has no value")

                    ids.add(val)
                return ids

            subgraph_ids = extract_subgraph_ids(app.graph)
            for sg_id in subgraph_ids:
                custom_path = f"{self.file_path}/sub_graph/{sg_id}.json"
                if await asyncio.to_thread(os.path.exists, custom_path):
                    continue
                premade_path = f"data/sub_graph/{sg_id}.json"
                if not await asyncio.to_thread(os.path.exists, premade_path):
                    return aiohttp.web.json_response(
                        {
                            "status": "error",
                            "message": f"Premade subgraph {sg_id} doesn't exist",
                        },
                        status=400,
                    )

            response = messages.SaveAppResponse(app=app)
            return aiohttp.web.Response(
                body=response.model_dump_json(), content_type="application/json"
            )
        except Exception as e:
            logging.error(f"Error importing app: {e}", exc_info=True)
            return aiohttp.web.json_response(
                {"status": "error", "message": str(e)}, status=400
            )

    async def export_app(self, request: aiohttp.web.Request):
        app_id = request.match_info.get("id")
        if not app_id:
            return aiohttp.web.json_response(
                {"status": "error", "message": "Missing app ID"}, status=400
            )

        try:
            async with aiofiles.open(
                f"{self.file_path}/app/{app_id}.json", mode="r"
            ) as json_file:
                json_content = await json_file.read()

            obj = models.RepositoryApp.model_validate_json(json_content)
            for node in obj.graph.nodes:
                for p in node.pads:
                    if p.allowed_types:
                        for at in p.allowed_types:
                            if at.type == "secret":
                                at.options = []
                    if p.default_allowed_types:
                        for at in p.default_allowed_types:
                            if at.type == "secret":
                                at.options = []

            # Extract potential subgraph IDs
            def extract_subgraph_ids(graph: GraphEditorRepresentation) -> set[str]:
                ids = set()
                for node in graph.nodes:
                    if node.type != "SubGraph":
                        continue

                    id_pads = [p for p in node.pads if p.id == "__subgraph_id__"]
                    if len(id_pads) == 0:
                        raise ValueError("No __subgraph_id__ pad found")

                    if len(id_pads) > 1:
                        raise ValueError("Multiple __subgraph_id__ pads found")

                    val = id_pads[0].value
                    if not val:
                        raise ValueError("__subgraph_id__ pad has no value")

                    ids.add(val)
                return ids

            subgraph_ids = extract_subgraph_ids(obj.graph)
            subgraphs = []
            for sg_id in subgraph_ids:
                path = f"{self.file_path}/sub_graph/{sg_id}.json"
                if not await asyncio.to_thread(os.path.exists, path):
                    continue
                async with aiofiles.open(path, mode="r") as f:
                    content = await f.read()

                sg = models.RepositorySubGraph.model_validate_json(content)

                for node in sg.graph.nodes:
                    for p in node.pads:
                        if p.allowed_types:
                            for at in p.allowed_types:
                                if at.type == "secret":
                                    at.options = []
                        if p.default_allowed_types:
                            for at in p.default_allowed_types:
                                if at.type == "secret":
                                    at.options = []

                subgraphs.append(sg)

            export_obj = models.AppExport(app=obj, subgraphs=subgraphs)
            resp = messages.ExportAppResponse(export=export_obj)
            return aiohttp.web.Response(
                body=resp.model_dump_json(), content_type="application/json"
            )
        except FileNotFoundError:
            return aiohttp.web.json_response(
                {"status": "error", "message": "App not found"}, status=404
            )
        except Exception as e:
            logging.error(f"Error exporting app: {e}", exc_info=True)
            return aiohttp.web.json_response(
                {"status": "error", "message": str(e)}, status=500
            )

    async def get_subgraph(self, request: aiohttp.web.Request):
        subgraph_id = request.match_info.get("id")
        if not subgraph_id:
            return aiohttp.web.json_response(
                {"status": "error", "message": "Missing subgraph ID"}, status=400
            )

        try:
            async with aiofiles.open(
                f"{self.file_path}/sub_graph/{subgraph_id}.json", mode="r"
            ) as json_file:
                json_content = await json_file.read()
            obj = models.RepositorySubGraph.model_validate_json(json_content)
            resp = messages.GetSubgraphResponse(sub_graph=obj)
            return aiohttp.web.Response(
                body=resp.model_dump_json(), content_type="application/json"
            )
        except FileNotFoundError:
            return aiohttp.web.json_response(
                {"status": "error", "message": "Subgraph not found"}, status=404
            )

    async def list_subgraphs(self, request: aiohttp.web.Request):
        try:
            sub_graph_dir = f"{self.file_path}/sub_graph"
            try:
                files = await asyncio.to_thread(os.listdir, sub_graph_dir)
            except FileNotFoundError:
                await self.ensure_dir(sub_graph_dir)
                files = []
            subgraphs = []
            for file in files:
                if file.endswith(".json"):
                    async with aiofiles.open(
                        f"{self.file_path}/sub_graph/{file}", mode="r"
                    ) as f:
                        content = await f.read()
                        subgraph = models.RepositorySubGraph.model_validate_json(
                            content
                        )
                        subgraphs.append(subgraph)
            sorted_by_created_at = sorted(
                subgraphs, key=lambda x: x.created_at, reverse=True
            )
            response = messages.ListSubgraphsResponse(sub_graphs=sorted_by_created_at)
            return aiohttp.web.Response(
                body=response.model_dump_json(), content_type="application/json"
            )
        except Exception as e:
            logging.error(f"Error listing subgraphs: {e}")
            return aiohttp.web.json_response(
                {"status": "error", "message": str(e)}, status=500
            )

    async def save_subgraph(self, request: aiohttp.web.Request):
        try:
            data = await request.json()
            req = messages.SaveSubgraphRequest.model_validate(data)
            subgraph: models.RepositorySubGraph | None = None
            if req.id:
                try:
                    async with aiofiles.open(
                        f"{self.file_path}/sub_graph/{req.id}.json", mode="r"
                    ) as f:
                        content = await f.read()
                        subgraph = models.RepositorySubGraph.model_validate_json(
                            content
                        )
                except FileNotFoundError:
                    pass
            else:
                req.id = str(uuid4())
                subgraph = models.RepositorySubGraph(
                    id=req.id,
                    name=req.name,
                    created_at=datetime.datetime.now(),
                    updated_at=datetime.datetime.now(),
                    graph=req.graph,
                )

            if not subgraph:
                return aiohttp.web.json_response(
                    {"status": "error", "message": "Subgraph not found"}, status=404
                )

            subgraph.updated_at = datetime.datetime.now()
            subgraph.name = req.name
            subgraph.graph = req.graph
            save_path = f"{self.file_path}/sub_graph/{req.id}.json"

            await self.ensure_dir(f"{self.file_path}/sub_graph")
            async with aiofiles.open(save_path, mode="w") as f:
                await f.write(subgraph.model_dump_json())
            response = messages.SaveSubgraphResponse(
                sub_graph=models.RepositorySubGraph.model_validate(subgraph)
            )
            return aiohttp.web.Response(
                body=response.model_dump_json(), content_type="application/json"
            )
        except Exception as e:
            logging.error(f"Error saving subgraph: {e}", exc_info=True)
            return aiohttp.web.json_response(
                {"status": "error", "message": str(e)}, status=400
            )

    async def delete_subgraph(self, request: aiohttp.web.Request):
        subgraph_id = request.match_info.get("id")
        if not subgraph_id:
            return aiohttp.web.json_response(
                {"status": "error", "message": "Missing subgraph ID"}, status=400
            )
        try:
            file_path = f"{self.file_path}/sub_graph/{subgraph_id}.json"
            await asyncio.to_thread(os.remove, file_path)
            return aiohttp.web.json_response({"status": "success", "id": subgraph_id})
        except FileNotFoundError:
            return aiohttp.web.json_response(
                {"status": "error", "message": "Subgraph not found"}, status=404
            )
        except Exception as e:
            logging.error(f"Error deleting subgraph: {e}")
            return aiohttp.web.json_response(
                {"status": "error", "message": str(e)}, status=500
            )

    async def run(self):
        await asyncio.to_thread(os.makedirs, f"{self.file_path}/app", exist_ok=True)
        await asyncio.to_thread(
            os.makedirs, f"{self.file_path}/sub_graph", exist_ok=True
        )
        runner = web.AppRunner(self.app)
        await runner.setup()
        site = web.TCPSite(runner, "0.0.0.0", self.port)
        print(f"Starting repository server on 0.0.0.0:{self.port}")
        await site.start()

        # Keep the server running
        try:
            while True:
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            logging.info("Repository server has been cancelled.")
        except Exception as e:
            logging.error(f"Error in repository server: {e}", exc_info=True)

        try:
            await runner.cleanup()
        except Exception as e:
            logging.error(f"Error during repository server cleanup: {e}", exc_info=True)

        logging.info("Repository server has been shut down.")

    async def list_examples(self, request: aiohttp.web.Request):
        try:
            example_dir = "data/example"
            files = await asyncio.to_thread(os.listdir, example_dir)
            apps = []
            for file in files:
                if file.endswith(".json"):
                    async with aiofiles.open(f"{example_dir}/{file}", mode="r") as f:
                        content = await f.read()
                        app = models.RepositoryApp.model_validate_json(content)
                        apps.append(app)
            sorted_by_created_at = sorted(
                apps, key=lambda x: x.created_at, reverse=True
            )
            response = messages.ListAppsResponse(apps=sorted_by_created_at)
            return aiohttp.web.Response(
                body=response.model_dump_json(), content_type="application/json"
            )
        except Exception as e:
            logging.error(f"Error listing apps: {e}")
            return aiohttp.web.json_response(
                {"status": "error", "message": str(e)}, status=500
            )

    async def get_example(self, request: aiohttp.web.Request):
        example_dir = "data/example"
        example_id = request.match_info.get("id")
        if not example_id:
            return aiohttp.web.json_response(
                {"status": "error", "message": "Missing app ID"}, status=400
            )

        try:
            async with aiofiles.open(
                f"{example_dir}/{example_id}.json", mode="r"
            ) as json_file:
                json_content = await json_file.read()
            obj = models.RepositoryApp.model_validate_json(json_content)
            resp = messages.GetAppResponse(app=obj)
            return aiohttp.web.Response(
                body=resp.model_dump_json(), content_type="application/json"
            )
        except FileNotFoundError:
            return aiohttp.web.json_response(
                {"status": "error", "message": "App not found"}, status=404
            )

    async def list_premade_subgraphs(self, request: aiohttp.web.Request):
        try:
            subgraph_dir = "data/sub_graph"
            files = await asyncio.to_thread(os.listdir, subgraph_dir)
            subgraphs = []
            for file in files:
                if file.endswith(".json"):
                    async with aiofiles.open(f"{subgraph_dir}/{file}", mode="r") as f:
                        content = await f.read()
                        subgraph = models.RepositorySubGraph.model_validate_json(
                            content
                        )
                        subgraphs.append(subgraph)
            sorted_by_created_at = sorted(
                subgraphs, key=lambda x: x.created_at, reverse=True
            )
            response = messages.ListSubgraphsResponse(sub_graphs=sorted_by_created_at)
            return aiohttp.web.Response(
                body=response.model_dump_json(), content_type="application/json"
            )
        except Exception as e:
            logging.error(f"Error listing premade subgraphs: {e}")
            return aiohttp.web.json_response(
                {"status": "error", "message": str(e)}, status=500
            )

    async def get_premade_subgraph(self, request: aiohttp.web.Request):
        subgraph_dir = "data/sub_graph"
        subgraph_id = request.match_info.get("id")
        if not subgraph_id:
            return aiohttp.web.json_response(
                {"status": "error", "message": "Missing subgraph ID"}, status=400
            )

        try:
            async with aiofiles.open(
                f"{subgraph_dir}/{subgraph_id}.json", mode="r"
            ) as json_file:
                json_content = await json_file.read()
            obj = models.RepositorySubGraph.model_validate_json(json_content)
            resp = messages.GetSubgraphResponse(sub_graph=obj)
            return aiohttp.web.Response(
                body=resp.model_dump_json(), content_type="application/json"
            )
        except FileNotFoundError:
            return aiohttp.web.json_response(
                {"status": "error", "message": "Subgraph not found"}, status=404
            )

    async def app_run(self, request: aiohttp.web.Request):
        livekit_url = "ws://192.168.1.29:7880"
        internal_livekit_url = os.environ.get("LIVEKIT_URL", livekit_url)
        livekit_api_key = "devkey"
        livekit_api_secret = "secret"
        req = messages.CreateAppRunRequest.model_validate(await request.json())

        at = api.AccessToken(livekit_api_key, livekit_api_secret)
        at = at.with_grants(
            api.VideoGrants(
                room_join=True,
                room=req.run_id,
                room_create=False,
                can_publish=True,
                can_subscribe=True,
            )
        ).with_identity(f"human-{short_uuid()}")
        lkapi = api.LiveKitAPI(
            url=internal_livekit_url,
            api_key=livekit_api_key,
            api_secret=livekit_api_secret,
        )
        try:
            await lkapi.room.create_room(
                create=api.CreateRoomRequest(
                    name=req.run_id,
                    agents=[
                        api.RoomAgentDispatch(
                            agent_name="gabber-engine", metadata=req.model_dump_json()
                        )
                    ],
                )
            )
        except Exception as e:
            logging.error(f"Error creating app run: {e}")
        connection_details = models.AppRunConnectionDetails(
            url=livekit_url,
            token=at.to_jwt(),
        )
        response = messages.CreateAppRunResponse(connection_details=connection_details)
        return aiohttp.web.Response(
            body=response.model_dump_json(), content_type="application/json"
        )

    async def debug_connection(self, request: aiohttp.web.Request):
        livekit_url = "ws://192.168.1.29:7880"
        internal_livekit_url = os.environ.get("LIVEKIT_URL", livekit_url)
        livekit_api_key = "devkey"
        livekit_api_secret = "secret"
        req = messages.DebugConnectionRequest.model_validate(await request.json())
        at = api.AccessToken(livekit_api_key, livekit_api_secret)
        at = at.with_grants(
            api.VideoGrants(
                room_join=True,
                room=req.run_id,
                can_publish=False,
                can_publish_data=True,
                can_subscribe=True,
            )
        ).with_identity("debug")

        connection_details = models.AppRunConnectionDetails(
            url=livekit_url,
            token=at.to_jwt(),
        )

        lkapi = api.LiveKitAPI(
            url=internal_livekit_url,
            api_key=livekit_api_key,
            api_secret=livekit_api_secret,
        )
        dispatches = await lkapi.agent_dispatch.list_dispatch(room_name=req.run_id)
        if not dispatches:
            return aiohttp.web.json_response(
                {"status": "error", "message": "No dispatch found for the room"},
                status=404,
            )

        dispatch = next(
            (d for d in dispatches if d.agent_name == "gabber-engine"), None
        )
        if not dispatch:
            return aiohttp.web.json_response(
                {"status": "error", "message": "No gabber-engine dispatch found"},
                status=404,
            )
        dispatch_metadata = json.loads(dispatch.metadata)
        graph = GraphEditorRepresentation.model_validate(dispatch_metadata["graph"])
        response = messages.DebugConnectionResponse(
            connection_details=connection_details,
            graph=graph,
        )
        return aiohttp.web.Response(
            body=response.model_dump_json(), content_type="application/json"
        )

    async def mcp_proxy_connection(self, request: aiohttp.web.Request):
        livekit_url = "ws://localhost:7880"
        livekit_api_key = "devkey"
        livekit_api_secret = "secret"
        req = messages.MCPProxyConnectionRequest.model_validate(await request.json())
        at = api.AccessToken(livekit_api_key, livekit_api_secret)
        at = at.with_grants(
            api.VideoGrants(
                room_join=True,
                room=req.run_id,
                can_publish=False,
                can_publish_data=True,
                can_subscribe=True,
            )
        ).with_identity("mcp_proxy")

        connection_details = models.AppRunConnectionDetails(
            url=livekit_url,
            token=at.to_jwt(),
        )

        response = messages.MCPProxyConnectionResponse(
            connection_details=connection_details
        )
        return aiohttp.web.Response(
            body=response.model_dump_json(), content_type="application/json"
        )
