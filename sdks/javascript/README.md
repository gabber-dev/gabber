# Gabber JavaScript SDK

The Gabber JavaScript SDK provides a framework-agnostic client library for integrating Gabber's real-time AI capabilities into any JavaScript/TypeScript application. This SDK is ideal for Node.js, browsers, Bun, and Deno environments.

## Installation

```bash
npm install @gabber/client
# or
yarn add @gabber/client
# or
pnpm add @gabber/client
```

## Key Features

- **Media Stream Management**: Easily handle audio, video, and screen sharing streams
- **Real-time Communication**: Built on LiveKit for robust WebRTC capabilities
- **Type Safety**: Full TypeScript support with comprehensive type definitions
- **Cross-Platform**: Works in browsers and Node.js environments
- **Flexible Integration**: Framework-agnostic design for use with any JavaScript project

## Quick Start

```typescript
import { Engine } from '@gabber/client';

// Initialize the engine
const engine = new Engine({
  handler: {
    onConnectionStateChange: (state) => {
      console.log('Connection state changed:', state);
    }
  }
});

// Connect to Gabber
await engine.connect({
  url: 'your-gabber-url',
  token: 'your-token'
});

// Get local media track (e.g., microphone)
const micTrack = await engine.getLocalTrack({
  type: 'microphone',
  echoCancellation: true,
  noiseSuppression: true
});

// Publish track to a node
const publication = await engine.publishToNode({
  localTrack: micTrack,
  publishNodeId: 'your-node-id'
});

// Subscribe to node output
const subscription = await engine.subscribeToNode({
  outputNodeId: 'output-node-id'
});
```

## Core Concepts

### Engine

The `Engine` class is the main entry point for interacting with Gabber. It handles:
- Connection management
- Media track creation and publishing
- Node subscription and communication
- Pad management for data flow

### Tracks

The SDK supports various types of media tracks:
- `microphone`: Audio input from microphone
- `webcam`: Video input from camera
- `screen`: Screen sharing (with optional audio)

### Pads

Pads are connection points for data flow:
- `SourcePad`: Emits data from nodes
- `SinkPad`: Receives data into nodes
- `PropertyPad`: Configures node behavior

## API Reference

### Engine Methods

- `connect(details: ConnectionDetails)`: Connect to Gabber
- `disconnect()`: Disconnect from Gabber
- `getLocalTrack(options: GetLocalTrackOptions)`: Create local media track
- `publishToNode(params: PublishParams)`: Publish track to node
- `subscribeToNode(params: SubscribeParams)`: Subscribe to node output
- `getSourcePad(nodeId: string, padId: string)`: Get source pad
- `getSinkPad(nodeId: string, padId: string)`: Get sink pad
- `getPropertyPad(nodeId: string, padId: string)`: Get property pad

## Examples

Check out the [examples directory](./example) for complete usage examples.

## License

This SDK is licensed under the Apache License 2.0 - see the [LICENSE](../LICENSE) file for details.
