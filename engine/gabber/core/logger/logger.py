import asyncio
import logging
import queue
from datetime import datetime
from ..graph.runtime_api import RuntimeApi, RuntimeEventPayload_LogItem

import sys


class GabberFilter(logging.Filter):
    def __init__(self, *, node: str | None, subgraph: str | None = None):
        self.node = node
        self.subgraph = subgraph

    def filter(self, record):
        record.node = self.node
        record.subgraph = self.subgraph
        return True


class GabberLogHandler(logging.StreamHandler):
    def __init__(self, runtime_api: RuntimeApi):
        super().__init__(sys.stderr)
        self._runtime_api = runtime_api
        self.q = queue.Queue[RuntimeEventPayload_LogItem]()

    def emit(self, record):
        super().emit(record)

        node = getattr(record, "node", None)
        subgraph = getattr(record, "subgraph", None)
        pad = getattr(record, "pad", None)

        self.q.put_nowait(
            RuntimeEventPayload_LogItem(
                message=record.getMessage(),
                timestamp=datetime.fromtimestamp(record.created).isoformat(),
                level=record.levelname,
                node=node,
                subgraph=subgraph,
                pad=pad,
            )
        )

    async def run(self):
        while True:
            entries: list[RuntimeEventPayload_LogItem] = []
            try:
                while True:
                    entry = self.q.get_nowait()
                    entries.append(entry)
            except queue.Empty:
                pass

            if entries:
                for entry in entries:
                    try:
                        self._runtime_api.emit_logs(entries)
                    except Exception as e:
                        logging.error(f"Failed to publish log entry: {e}")

            await asyncio.sleep(0.1)
