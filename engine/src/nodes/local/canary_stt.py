from core import node, pad
from typing import cast


class CanarySTT(node.Node):
    async def resolve_pads(self):
        audio_in = self.get_pad("audio_in")
        pass

    async def run(self):
        pass
