from .connection_provider import ConnectionProvider
from gabber import ConnectionDetails
import aiohttp


class LocalConnectionProvider(ConnectionProvider):
    async def get_connection(self, *, run_id: str) -> ConnectionDetails:
        async with aiohttp.ClientSession() as session:
            req = {"type": "mcp_proxy_connection", "run_id": run_id}
            async with session.post(
                "http://localhost:8001/app/mcp_proxy_connection", json=req
            ) as response:
                data = await response.json()
                return ConnectionDetails(**data["connection_details"])
