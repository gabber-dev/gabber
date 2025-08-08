# Gabber JavaScript SDK

Framework‑agnostic client for browsers/Node.

## Install

```bash
npm install @gabber/client
```

## Quickstart

```ts
import { Engine } from '@gabber/client'

const engine = new Engine()
await engine.connect({ url: 'your-gabber-url', token: 'your-token' })

const mic = await engine.getLocalTrack({ type: 'microphone' })
await engine.publishToNode({ localTrack: mic, publishNodeId: 'node-id' })

await engine.subscribeToNode({ outputNodeId: 'output-node-id' })
```

More examples: ./example
