# Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
# SPDX-License-Identifier: SUL-1.0

import asyncio
import logging
import queue
from datetime import datetime
from ..graph.runtime_api import RuntimeApi, RuntimeEventPayload_LogItem


class GabberLogHandler(logging.Handler):
    def __init__(self, runtime_api: RuntimeApi):
        super().__init__()
        self._runtime_api = runtime_api
        self.q = queue.Queue[RuntimeEventPayload_LogItem]()
        self._closed = False

    def emit(self, record):
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

    def close(self):
        self._closed = True
        super().close()

    async def run(self):
        while not self._closed:
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
