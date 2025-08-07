
<p align="center">
  <img src="frontend/public/banner.png" alt="Gabber Logo" width="100%"/>
</p>

# Gabber - 

[Gabber](https://gabber.dev) is an engine for building real-time AI across all modalities — voice, text, video, and more. It supports graph-based apps with multiple participants and simultaneous media streams. Our goal is to give developers the **most powerful, developer-friendly AI app builder** available.

If you found this interesting, please consider leaving a star ⭐️. We will be updating this repo frequently with new nodes and functionality.

## Quickstart 

### Install dependencies

__LiveKit__:
The frontend sends/receives media to/from the backend services via a local WebRTC session.
```bash
brew install livekit
```

__uv__:
For python dependency management.
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Run Everything
```bash
make all
```

## High-level Concepts

### App

An App is a graph consisting of nodes and their Pad connections. It's the highest level object in Gabber.

### Node

A Node is a functional building block within a Gabber app or subgraph. Each node performs a specific operation — like ingesting media, transcribing audio, analyzing emotions, calling an external API, or generating a response. Nodes can be composed into flows that define how your AI app behaves in real time.

Nodes have Inputs and Outputs called pads. Some pads have configurable properties that effect the behavior of the node.

You can think of nodes like nodes in a media pipeline, but with AI logic, state transitions, and tool-calling built in.

### Pad

A Pad is a connection point on a node that allows it to send or receive data. There are two types of pads:

- Sink Pads: Receive data from upstream nodes
- Source Pads: Send data to downstream nodes
- Property Pads: Dynamic pads that adjust the behavior of the containing node
- Stateless Pads: Static nodes that simply receive or emit data

Pads are typed — for example, audio pads, control/event pads, and text pads — so only compatible nodes can be linked. This type-safe wiring ensures your graph behaves predictably and enforces valid data flows between components.

Pads allow Gabber apps to function like reactive pipelines: when a node emits output on a pad, any downstream nodes connected to that pad can process the result in real time.

### SubGraph

A SubGraph is very similar to an App — it’s a collection of nodes and their pad connections. However, unlike an App, a SubGraph is designed to be embedded within other apps as a single node.

By using Proxy nodes, you can expose specific pads from within the SubGraph so they appear in the parent app. This makes it easy to pass data in and out of the SubGraph just like any other node.

The primary purpose of SubGraphs is to:
- Create reusable logic and implementations
- Abstract complex behaviors into simple, modular units

This helps keep your main app graphs clean, composable, and easier to maintain.

### State Machines
The Gabber platform includes a State Machine system for orchestrating service workflows.

#### Key Concepts
Parameters
State Machines have parameters that affect the behavior of states (e.g., voice style, model choice).

**States**
States define distinct phases of your application flow.
You can chain states starting with an initial state connected directly from the State Machine block.

**State Transitions**
Transition nodes control movement between states based on conditions or events.

**Transition Node Logic**
Transition nodes act as AND gates — all connected conditions must be satisfied before transitioning.
You can create OR gates by running two transition nodes in parallel into the same target state.

<p align="center">
  <img src="frontend/public/state_machine_example.png" alt="Example State Machine Gabber" width="100%"/>
</p>

#### Example Flow
1. Start with an Initial State node *Greeting*.
2. Add a second State called *Capture*.
3. Add a State Transition Node between *Greeting* and *Capture* for a specific input (e.g., Parameter_0 triggered).
4. When Parameter_0 is triggered, the state machine will transition to *Capture*.
5. Using an EnumSwitch, I can trigger downstream changes based on the state.
6. Optionally, add parallel transition nodes to allow multiple triggers for the same state.

This setup makes it easy to design branching, conditional logic for your AI-powered workflows.

## Anatomy

Gabber consists of a frontend and three backend services: engine, editor, repository.

### Frontend

The frontend is a NextJS app and is the user interface for interacting with the backend services. The frontend
can be accessed `http://localhost:3000`.

### Editor

The editor is responsible for visually designing the experience. The editor consists of building blocks called nodes that can be configured to create apps that can ingest media streams from audio, video, and screen sources. Using these inputs, create state machines, tool calls, and text, voice, or soon video responses.

### Engine

The engine is the service responsible for running apps.

### Repository

The repository service is a very thin local http server reponsible for fetching and saving apps and subgraphs.
All entities are stored in the `.gabber` directory. It runs on port `8001`.

## SDKs
Gabber provides SDKs to help you integrate these services into your applications quickly. These SDKs handle authentication, API calls, and streaming where supported.

Currently available SDKs include:
- **JavaScript/TypeScript SDK** — framework-agnostic client library for Node.js, browsers, Bun, and Deno. Ideal for backend services or non-React frontends.
- **React SDK** — prebuilt hooks, providers, and UI components for building Gabber-powered apps in React or React Native with minimal setup.
- **Python SDK** — for backend integrations, prototyping, and scripting.

Refer to the SDK documentation in the main Gabber repo for installation and usage details.

## Example Apps
This repository includes example applications demonstrating how to use Gabber services together.
To explore them:
1. Run the repository locally (`make all` or run each service individually).
2. Navigate to the **Examples** tab in the dashboard.
3. Choose a sample app and follow the instructions.

These examples showcase real-world usage patterns for voice, text, and multimodal AI.

## Community
Gabber is source-available and developer-first — we’d love for you to build with us.

- **Questions or feedback?** Open a [GitHub Discussion](https://github.com/gabber-dev/gabber/discussions) or start a thread in [Issues](https://github.com/gabber-dev/gabber/issues).
- **See something missing?** We welcome contributions — new nodes or bugfixes are all appreciated.
- **Early access or enterprise?** [Reach out](mailto:brian@gabber.dev) or file an issue with the label `enterprise`.
- **Stay in the loop:** Follow [@gabberdev](https://x.com/gabberdev) on Twitter/X or star the repo to get updates.
- **Join the community** Join the [Discord](https://discord.gg/hJdjwBRc7g) to leave feedback, chat with the team & other builders, and stay up to date.

## License

The Gabber engine and frontend code are [fair-code](https://faircode.io) distributed under the [Sustainable Use License](https://github.com/gabber-dev/gabber/blob/master/LICENSE.md) and [Gabber Enterprise License](https://github.com/gabber-dev/gabber/blob/master/LICENSE_EE.md).

This code follows the same license as [n8n](https://github.com/n8n-io/n8n)

- **Source Available**: Always visible source code
- **Self-Hostable**: Deploy anywhere
- **Extensible**: Add your own nodes and functionality

Code that isn't core to the Gabber engine and editor, such as examples and SDKs, are licensed as Apache 2.0 which is denoted by a LICENSE file in the corresponding directories.
