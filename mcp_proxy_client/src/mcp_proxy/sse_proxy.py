from gabber import MCPServer, MCPTransportDatachannelProxy, MCPTransportSSE

import mcp


class SSEProxy:
    def __init__(self, *, server: MCPServer):
        self.server = server

    async def start(self):
        client_session = mcp.ClientSession()
        pass
