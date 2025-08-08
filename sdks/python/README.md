# Gabber Python SDK

Python client for Gabber.

## Install

```bash
pip install gabber-client
# or
uv pip install gabber-client
```

## Quickstart

```python
import asyncio
from gabber import Engine

async def main():
    engine = Engine()
    await engine.connect(url="your-gabber-url", token="your-token")
    sub = await engine.subscribe_to_node(output_node_id="node-id")
    async for out in sub:
        print(out)

asyncio.run(main())
```

See examples in the main repo.