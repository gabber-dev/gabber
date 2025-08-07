# Gabber Python SDK

The Gabber Python SDK provides a powerful interface for integrating Gabber's real-time AI capabilities into Python applications. Perfect for backend services, data processing pipelines, and AI/ML workflows.

## Installation

```bash
pip install gabber-client
# or using uv (recommended)
uv pip install gabber-client
```

## Key Features

- **Async Support**: Built with modern Python async/await patterns
- **Type Hints**: Comprehensive type annotations for better IDE support
- **Backend Integration**: Seamless integration with Python backend services
- **Cross-Platform**: Works on all major operating systems
- **AI/ML Ready**: Designed for AI and machine learning workflows

## Quick Start

```python
import asyncio
from gabber import Engine

async def main():
    # Initialize the engine
    engine = Engine()
    
    # Connect to Gabber
    await engine.connect(
        url="your-gabber-url",
        token="your-token"
    )
    
    # Subscribe to node output
    subscription = await engine.subscribe_to_node(
        output_node_id="your-node-id"
    )
    
    # Handle node output
    async for output in subscription:
        print(f"Received output: {output}")

if __name__ == "__main__":
    asyncio.run(main())
```

## Core Concepts

### Engine

The main interface for interacting with Gabber:
- Connection management
- Node subscription and communication
- Pad management for data flow

### Pads

Connection points for data flow:
- `SourcePad`: Emits data from nodes
- `SinkPad`: Receives data into nodes
- `PropertyPad`: Configures node behavior

## API Reference

### Engine Methods

```python
class Engine:
    async def connect(self, url: str, token: str) -> None:
        """Connect to Gabber"""
        
    async def disconnect(self) -> None:
        """Disconnect from Gabber"""
        
    async def subscribe_to_node(self, output_node_id: str) -> Subscription:
        """Subscribe to node output"""
        
    def get_source_pad(self, node_id: str, pad_id: str) -> SourcePad:
        """Get source pad"""
        
    def get_sink_pad(self, node_id: str, pad_id: str) -> SinkPad:
        """Get sink pad"""
        
    def get_property_pad(self, node_id: str, pad_id: str) -> PropertyPad:
        """Get property pad"""
```

## Usage Examples

### Working with Pads

```python
# Get a property pad
property_pad = engine.get_property_pad("node-id", "pad-id")
await property_pad.set_value("new value")

# Get a source pad
source_pad = engine.get_source_pad("node-id", "pad-id")
async for value in source_pad:
    print(f"Received value: {value}")

# Get a sink pad
sink_pad = engine.get_sink_pad("node-id", "pad-id")
await sink_pad.send_value("data to send")
```

### Error Handling

```python
from gabber.exceptions import GabberConnectionError

try:
    await engine.connect(url, token)
except GabberConnectionError as e:
    print(f"Failed to connect: {e}")
```

## Best Practices

1. Use async/await for all asynchronous operations
2. Properly handle connection state and errors
3. Clean up resources using async context managers
4. Utilize type hints for better code maintainability
5. Follow Python's asyncio best practices

## Examples

Check out the [examples directory](../examples) in the main repository for complete usage examples.

## License

This SDK is licensed under the Apache License 2.0 - see the [LICENSE](../LICENSE) file for details.