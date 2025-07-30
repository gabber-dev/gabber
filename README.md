
<p align="center">
  <img src="frontend/public/banner.png" alt="Gabber Logo" width="100%"/>
</p>

# Gabber - 

[Gabber](https://gabber.dev) is an engine for making real-time AI across all modalities.

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

### SubGraph

A SubGraph is very similar to an App. It's a collection of nodes and their pad connections. SubGraphs themselves become
nodes that can be embedded into apps. The primary purpose of Subgraphs is to create re-usable implementations and
to abstract complicated implementations into single, simple nodes.

### Node

### Pad

## Anatomy

Gabber consists of a frontend and three backend services: engine, editor, repository.

### Frontend

The frontend is a NextJS app and is the user interface for interacting with the backend services. The frontend
can be accessed `http://localhost:3000`.

### Editor

The editor is responsible for 

### Engine

The engine is the service responsible for running apps.

### Repository

The repository service is a very thin local http server reponsible for fetching and saving apps and subgraphs.
All entities are stored in the `.gabber` directory. It runs on port `8001`.

## Community

## License

The Gabber engine and frontend code are [fair-code](https://faircode.io) distributed under the [Sustainable Use License](https://github.com/gabber-dev/gabber/blob/master/LICENSE.md) and [Gabber Enterprise License](https://github.com/gabber-dev/gabber/blob/master/LICENSE_EE.md).

This code follows the same license as [n8n](https://github.com/n8n-io/n8n)

- **Source Available**: Always visible source code
- **Self-Hostable**: Deploy anywhere
- **Extensible**: Add your own nodes and functionality

Code that isn't core to the Gabber engine and editor, such as examples and SDKs, are licensed as Apache 2.0 which is denoted by a LICENSE file in the corresponding directories.
