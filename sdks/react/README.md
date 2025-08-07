# Gabber React SDK

The Gabber React SDK provides a set of hooks and components for seamlessly integrating Gabber's real-time AI capabilities into React applications. Built on top of the Gabber JavaScript SDK, it offers React-specific optimizations and patterns.

## Installation

```bash
npm install @gabber/client-react @gabber/client
# or
yarn add @gabber/client-react @gabber/client
# or
pnpm add @gabber/client-react @gabber/client
```

## Key Features

- **React Hooks**: Purpose-built hooks for managing Gabber state and interactions
- **Context Provider**: Global engine state management
- **Type Safety**: Full TypeScript support
- **React-Optimized**: Efficient rendering and state updates
- **Easy Integration**: Simple drop-in components and hooks

## Quick Start

```tsx
import { EngineProvider, useEngine } from '@gabber/client-react';

// Wrap your app with the provider
function App() {
  return (
    <EngineProvider>
      <YourComponent />
    </EngineProvider>
  );
}

// Use hooks in your components
function YourComponent() {
  const { 
    connectionState, 
    connect, 
    getLocalTrack,
    publishToNode 
  } = useEngine();

  useEffect(() => {
    // Connect to Gabber
    connect({
      url: 'your-gabber-url',
      token: 'your-token'
    });
  }, []);

  return (
    <div>
      Connection State: {connectionState}
    </div>
  );
}
```

## Core Hooks

### useEngine

The main hook for accessing Gabber functionality:

```typescript
const {
  connectionState,
  getLocalTrack,
  connect,
  disconnect,
  publishToNode,
  subscribeToNode
} = useEngine();
```

### usePad

Hook for interacting with node pads:

```typescript
const { value, setValue } = usePad(nodeId, padId);
```

### usePropertyPad

Hook for managing property pads:

```typescript
const { value, setValue } = usePropertyPad(nodeId, padId);
```

### useSourcePad

Hook for handling source pads:

```typescript
const { value } = useSourcePad(nodeId, padId);
```

## Context Provider

The `EngineProvider` component manages global Gabber state:

```tsx
<EngineProvider>
  <App />
</EngineProvider>
```

## Type Support

The SDK includes comprehensive TypeScript definitions:

```typescript
import type { 
  ConnectionState,
  GetLocalTrackOptions,
  PublishParams,
  SubscribeParams 
} from '@gabber/client';
```

## Best Practices

1. Always wrap your app with `EngineProvider`
2. Use the appropriate hooks for different pad types
3. Handle connection state changes appropriately
4. Clean up resources in useEffect cleanup functions
5. Use TypeScript for better type safety and autocompletion

## Examples

Check out the [examples directory](../examples) in the main repository for complete usage examples.

## License

This SDK is licensed under the Apache License 2.0 - see the [LICENSE](../LICENSE) file for details.