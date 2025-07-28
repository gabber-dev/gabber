# Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
# SPDX-License-Identifier: SUL-1.0

import asyncio
import logging
import os

import aiofiles
import aiohttp
import aiohttp.web
import messages
import models
from aiohttp import web

from utils import short_uuid


class RepositoryServer:
    def __init__(self, port: int, file_path: str = ".gabber/repository"):
        self.port = port
        self.file_path = file_path
        self.app = web.Application()
        self.setup_routes()

    def setup_routes(self):
        self.app.router.add_get("/app/list", self.list_apps)
        self.app.router.add_post("/app", self.save_app)
        self.app.router.add_get("/app/{id}", self.get_app)
        self.app.router.add_delete("/app/{id}", self.delete_app)
        self.app.router.add_get("/sub_graph/list", self.list_subgraphs)
        self.app.router.add_post("/sub_graph", self.save_subgraph)
        self.app.router.add_delete("/sub_graph/{id}", self.delete_subgraph)

    async def get_app(self, request: aiohttp.web.Request):
        app_id = request.match_info.get("id")
        if not app_id:
            return aiohttp.web.json_response(
                {"status": "error", "message": "Missing app ID"}, status=400
            )

        async with aiofiles.open(
            f"{self.file_path}/app/{app_id}.json", mode="r"
        ) as json_file:
            json_content = await json_file.read()
        obj = models.RepositoryApp.model_validate_json(json_content)
        resp = messages.GetAppResponse(app=obj)
        return aiohttp.web.json_response(resp.model_dump())

    async def list_apps(self, request: aiohttp.web.Request):
        try:
            files = await asyncio.to_thread(os.listdir, f"{self.file_path}/app")
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
            return aiohttp.web.json_response(response.model_dump())
        except Exception as e:
            logging.error(f"Error listing apps: {e}")
            return aiohttp.web.json_response(
                {"status": "error", "message": str(e)}, status=500
            )

    async def save_app(self, request: aiohttp.web.Request):
        try:
            data = await request.json()
            app = messages.SaveAppRequest.model_validate(data)
            if not app.id:
                app.id = short_uuid()
            save_path = f"{self.file_path}/app/{app.id}.json"
            async with aiofiles.open(save_path, mode="w") as f:
                await f.write(app.model_dump_json())
            response = messages.SaveAppResponse(
                app=models.RepositoryApp.model_validate(app)
            )
            return aiohttp.web.json_response(response.model_dump())
        except Exception as e:
            logging.error(f"Error saving app: {e}")
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

    async def list_subgraphs(self, request: aiohttp.web.Request):
        try:
            files = await asyncio.to_thread(os.listdir, f"{self.file_path}/sub_graph")
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
            response = messages.ListAppsResponse(apps=sorted_by_created_at)
            return aiohttp.web.json_response(response.model_dump())
        except Exception as e:
            logging.error(f"Error listing subgraphs: {e}")
            return aiohttp.web.json_response(
                {"status": "error", "message": str(e)}, status=500
            )

    async def save_subgraph(self, request: aiohttp.web.Request):
        try:
            data = await request.json()
            subgraph = messages.SaveSubgraphRequest.model_validate(data)
            if not subgraph.id:
                subgraph.id = short_uuid()
            save_path = f"{self.file_path}/sub_graph/{subgraph.id}.json"
            async with aiofiles.open(save_path, mode="w") as f:
                await f.write(subgraph.model_dump_json())
            return aiohttp.web.json_response({"status": "success", "id": subgraph.id})
        except Exception as e:
            logging.error(f"Error saving subgraph: {e}")
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
        except KeyboardInterrupt:
            print("Shutting down server...")
        finally:
            await runner.cleanup()
