# Gabber MCP Proxy Client

This is a small client application that proxies MCP traffic from the Gabber Engine to MCP Servers. The MCP servers can be running locally or remotely.

## Configure MCP Server

To configure MCP servers, create a file called `mcp.yaml`. See [example](mcp.example.yaml).

The full configuration spec can be referenced in [mcp_server_config.py](src/mcp_proxy/mcp_server_config.py)

## Start the Proxy

The proxy needs a run_id so it knows which Gabber session to connect to. First, start a Gabber that contains an LLM + MCP Server Node. Make sure the `mcp_server` value matches one of the servers configured in your `mcp.yaml`.

Copy the `run_id` that appears and run the proxy:

```bash
uv run src/main.py start <run_id>
```