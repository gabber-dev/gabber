# Gabber MCP Proxy Client

This is a small client application that proxies MCP traffic from the Gabber Engine to MCP Servers. The MCP servers can be running locally or remotely.

## Configure MCP Server

To configure MCP servers, create a file called `mcp.yaml` in your `mcp_proxy_client` directory (this directory). See [example](mcp.example.yaml). Add your new MCP server to the yaml file using the same format as the example MCP server.

The full configuration spec can be referenced in [mcp_server_config.py](src/mcp_proxy/mcp_server_config.py)

## Start the Proxy

The proxy needs a run_id so it knows which Gabber session to connect to. First, start a Gabber workflow that contains an LLM + MCP Server Node. Make sure the `mcp_server` value on the MCP node matches the name of a server configured in your `mcp.yaml`.

From the mcp the `run_id` that appears and run the proxy:

```bash
uv run src/main.py start <run_id>
```
