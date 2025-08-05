/**
 * Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
 * SPDX-License-Identifier: SUL-1.0
 */

"use client";

import {
  ConnectPadEdit,
  DisconnectPadEdit,
  GraphEditorRepresentation,
  GraphLibraryItem_Node,
  GraphLibraryItem_SubGraph,
  InsertNodeEdit,
  InsertSubGraphEdit,
  NodeEditorRepresentation,
  RemoveNodeEdit,
  Request,
  Response,
  UpdateNodeEdit,
  UpdatePadEdit,
} from "@/generated/editor";
import {
  applyEdgeChanges,
  applyNodeChanges,
  Connection,
  Edge,
  EdgeChange,
  Node,
  NodeChange,
} from "@xyflow/react";
import React, {
  createContext,
  useContext,
  useState,
  useEffect,
  useCallback,
  useMemo,
  useRef,
} from "react";
import useWebSocket, { ReadyState } from "react-use-websocket";
import toast from "react-hot-toast";

type ReactFlowRepresentation = {
  nodes: Node<NodeEditorRepresentation>[];
  edges: Edge[];
};

type EditorContextType = {
  debug: boolean;
  editorRepresentation: GraphEditorRepresentation;
  reactFlowRepresentation: ReactFlowRepresentation;
  isConnected: boolean;
  connectionStatus: "connecting" | "connected" | "disconnected" | "error";
  nodeLibrary?: (GraphLibraryItem_Node | GraphLibraryItem_SubGraph)[];

  unsavedChanges: boolean;
  saving: boolean;
  saveChanges: () => Promise<void>;

  onReactFlowConnect: (connection: Connection) => void;
  onReactFlowNodesChange: (changes: NodeChange[]) => void;
  onReactFlowEdgesChange: (changes: EdgeChange[]) => void;

  insertNode: (req: InsertNodeEdit) => void;
  insertSubGraph: (req: InsertSubGraphEdit) => void;
  removeNode: (req: RemoveNodeEdit) => void;
  connectPad: (req: ConnectPadEdit) => void;
  updatePad: (req: UpdatePadEdit) => void;
  updateNode: (req: UpdateNodeEdit) => void;
};

const EditorContext = createContext<EditorContextType | undefined>(undefined);

type Props = {
  children: React.ReactNode;
  debug: boolean;
  editor_url: string;
  savedGraph: GraphEditorRepresentation;
  saveImpl: (snapshot: GraphEditorRepresentation) => Promise<void>;
};

export function EditorProvider({
  children,
  debug,
  saveImpl,
  savedGraph,
  editor_url,
}: Props) {
  const [localRepresentation, setLocalRepresentation] =
    useState<GraphEditorRepresentation>(savedGraph);
  const [nodeLibrary, setNodeLibrary] = useState<
    (GraphLibraryItem_Node | GraphLibraryItem_SubGraph)[] | undefined
  >(undefined);
  const [saving, setSaving] = useState(false);
  const [reactFlowRepresentation, setReactFlowRepresentation] = useState<{
    nodes: Node[];
    edges: Edge[];
  }>({
    nodes: [],
    edges: [],
  });

  const { sendMessage, lastJsonMessage, readyState } = useWebSocket(
    editor_url,
    {
      shouldReconnect: (closeEvent) => {
        return closeEvent.code !== 1000;
      },
      reconnectAttempts: 5,
      reconnectInterval: (attemptNumber: number) => {
        return Math.min(Math.pow(2, attemptNumber) * 1000, 30000);
      },
    },
  );

  const [prevReadyState, setPrevReadyState] = useState<ReadyState>(
    ReadyState.UNINSTANTIATED,
  );

  useEffect(() => {
    if (readyState !== prevReadyState) {
      setPrevReadyState(readyState);
    }
  }, [readyState, prevReadyState]);

  useEffect(() => {
    const rfRep = graphToReact(localRepresentation);
    setReactFlowRepresentation(rfRep);
  }, [localRepresentation]);

  // Determine connection status and isConnected based on readyState
  const connectionStatus = (() => {
    switch (readyState) {
      case ReadyState.CONNECTING:
        return "connecting";
      case ReadyState.OPEN:
        return "connected";
      case ReadyState.CLOSING:
      case ReadyState.CLOSED:
        return "disconnected";
      default:
        return "error";
    }
  })();

  const isConnected = readyState === ReadyState.OPEN;

  const sendRequest = useCallback(
    (request: Request) => {
      if (isConnected) {
        sendMessage(JSON.stringify(request));
      } else {
        console.warn("WebSocket is not connected. Cannot send request.");
      }
    },
    [isConnected, sendMessage],
  );

  const insertNode = useCallback(
    (edit: InsertNodeEdit) => {
      sendRequest({
        type: "edit",
        edit,
      });
    },
    [sendRequest],
  );

  const insertSubGraph = useCallback(
    (edit: InsertSubGraphEdit) => {
      sendRequest({
        type: "edit",
        edit,
      });
    },
    [sendRequest],
  );

  const removeNode = useCallback(
    (edit: RemoveNodeEdit) => {
      sendRequest({
        type: "edit",
        edit,
      });
    },
    [sendRequest],
  );

  const connectPad = useCallback(
    (edit: ConnectPadEdit) => {
      sendRequest({
        type: "edit",
        edit,
      });
    },
    [sendRequest],
  );

  const pendingEdits = useRef<Map<string, UpdatePadEdit>>(new Map());
  const debounceTimers = useRef<Map<string, number>>(new Map());

  const updatePad = useCallback(
    (edit: UpdatePadEdit) => {
      const key = `${edit.node}-${edit.pad}`;

      // Update local representation immediately
      setLocalRepresentation((prev) => {
        if (!prev) return prev;
        const node = prev.nodes.find((n) => n.id === edit.node);
        if (!node) {
          console.warn(
            `Node with id ${edit.node} not found in local representation`,
          );
          return prev;
        }
        const pad = node.pads.find((p) => p.id === edit.pad);
        if (!pad) {
          console.warn(
            `Pad with id ${edit.pad} not found in node ${edit.node}`,
          );
          return prev;
        }

        const updatedPad = { ...pad, value: edit.value };
        const updatedPads = node.pads.map((p) =>
          p.id === edit.pad ? updatedPad : p,
        );
        const updatedNode = { ...node, pads: updatedPads };
        const updatedNodes = prev.nodes.map((n) =>
          n.id === edit.node ? updatedNode : n,
        );

        return { ...prev, nodes: updatedNodes };
      });

      // Set pending edit
      pendingEdits.current.set(key, edit);

      // Clear existing timer if any
      const existingTimer = debounceTimers.current.get(key);
      if (existingTimer) {
        clearTimeout(existingTimer);
      }

      // Set new debounce timer
      const timer = setTimeout(() => {
        const pendingEdit = pendingEdits.current.get(key);
        if (pendingEdit) {
          sendRequest({
            type: "edit",
            edit: pendingEdit,
          });
          pendingEdits.current.delete(key);
        }
        debounceTimers.current.delete(key);
      }, 250) as unknown as number;

      debounceTimers.current.set(key, timer);
    },
    [sendRequest],
  );

  const updateNode = useCallback(
    (edit: UpdateNodeEdit) => {
      sendRequest({
        type: "edit",
        edit,
      });

      // Update selection state if node ID is changing
      if (edit.new_id !== null && edit.new_id !== edit.id) {
        // TODO?
      }

      setLocalRepresentation((prev) => {
        if (!prev) return prev;
        const node = prev.nodes.find((n) => n.id === edit.id);
        if (!node) {
          console.warn(
            `Node with id ${edit.id} not found in local representation`,
          );
          return prev;
        }

        // Update node properties locally
        const updatedNode = { ...node };
        if (edit.editor_name !== null) {
          updatedNode.editor_name = edit.editor_name;
        }
        if (edit.new_id) {
          updatedNode.id = edit.new_id;
        }
        if (edit.editor_position !== null) {
          updatedNode.editor_position = edit.editor_position;
        }
        if (edit.editor_dimensions !== null) {
          updatedNode.editor_dimensions = edit.editor_dimensions;
        }

        // Update the nodes array
        const updatedNodes = prev.nodes.map((n) =>
          n.id === edit.id ? updatedNode : n,
        );

        return { ...prev, nodes: updatedNodes };
      });
    },
    [sendRequest],
  );

  useEffect(() => {
    if (readyState === ReadyState.OPEN && prevReadyState !== ReadyState.OPEN) {
      sendRequest({
        type: "load_from_snapshot",
        graph: localRepresentation,
      });

      sendRequest({ type: "get_node_library" });
    }
  }, [localRepresentation, prevReadyState, readyState, sendRequest]);

  useEffect(() => {
    if (!lastJsonMessage) return;

    try {
      const resp = (lastJsonMessage as Response).response;
      if (resp.type === "node_library") {
        setNodeLibrary(resp.node_library || []);
      } else if (resp.type === "full_graph") {
        setLocalRepresentation(resp.graph);
      }
    } catch (error) {
      console.error(
        "Error processing WebSocket message:",
        lastJsonMessage,
        error,
      );
    }
  }, [lastJsonMessage]);

  const onReactFlowNodesChange = useCallback(
    (changes: NodeChange[]) => {
      const prev = localRepresentation;
      if (!prev) {
        console.warn("No previous representation available");
        return;
      }
      const requests: Request[] = [];
      for (const change of changes) {
        if (change.type === "position") {
          reactFlowRepresentation.nodes = applyNodeChanges(
            [change],
            reactFlowRepresentation.nodes,
          );

          if (!change.dragging) {
            const edit: UpdateNodeEdit = {
              type: "update_node",
              id: change.id,
              editor_name: null,
              new_id: null,
              editor_position: [change.position?.x, change.position?.y],
              editor_dimensions: null,
            };
            requests.push({ type: "edit", edit });
          }
          setReactFlowRepresentation((prev) => ({
            ...prev,
            nodes: applyNodeChanges([change], prev.nodes),
          }));
        } else if (change.type === "select") {
          setReactFlowRepresentation((prev) => {
            const updatedNodes = applyNodeChanges([change], prev.nodes);
            return { ...prev, nodes: updatedNodes };
          });
        } else if (change.type === "remove") {
          const nodeId = change.id;
          requests.push({
            type: "edit",
            edit: {
              type: "remove_node",
              node_id: nodeId,
            } as RemoveNodeEdit,
          });
          prev.nodes = prev.nodes.filter((n) => n.id !== nodeId);
        } else if (change.type === "add") {
        } else if (change.type === "dimensions") {
          // Handle node dimension changes
          const nodeId = change.id;
          const newDims = change.dimensions;
          if (!newDims) {
            continue;
          }
          let oldDims = prev?.nodes.find(
            (n) => n.id === nodeId,
          )?.editor_dimensions;

          if (!oldDims) {
            oldDims = [-1, -1];
          }
          if (newDims.width === oldDims[0] && newDims.height === oldDims[1]) {
            continue; // No change in dimensions
          }
          const edit: UpdateNodeEdit = {
            type: "update_node",
            id: nodeId,
            editor_name: null,
            new_id: null,
            editor_position: null,
            editor_dimensions: [newDims.width, newDims.height],
          };
          requests.push({ type: "edit", edit });
          for (const node of prev?.nodes || []) {
            if (node.id === nodeId) {
              node.editor_dimensions = [newDims?.width, newDims?.height];
            }
          }
        }
      }
      for (const req of requests) {
        sendRequest(req);
      }
    },
    [localRepresentation, reactFlowRepresentation, sendRequest],
  );

  const onReactFlowEdgesChange = useCallback(
    (changes: EdgeChange[]) => {
      let dirty = false;
      const prev = localRepresentation;
      if (!prev) {
        console.warn("No previous representation available");
        return;
      }
      const requests: Request[] = [];
      for (const change of changes) {
        if (change.type === "select") {
          setReactFlowRepresentation((prev) => {
            const updatedEdges = applyEdgeChanges([change], prev.edges);
            return { ...prev, edges: updatedEdges };
          });
        } else if (change.type === "remove") {
          const fullId = change.id;
          const [sourceNodeId, sourcePadId, targetNodeId, targetPadId] =
            fullId.split("-");

          dirty = true;
          const sourceNode = prev?.nodes.find((n) => n.id === sourceNodeId);
          const sourcePad = sourceNode?.pads?.find((p) => p.id === sourcePadId);
          if (!sourcePad) {
            console.warn("Source pad not found for edge removal:", fullId);
            continue;
          }
          sourcePad.next_pads = sourcePad?.next_pads?.filter(
            (p) => p.node !== targetNodeId || p.pad !== targetPadId,
          );

          const targetNode = prev?.nodes.find((n) => n.id === targetNodeId);
          const targetPad = targetNode?.pads?.find((p) => p.id === targetPadId);
          if (!targetPad) {
            console.warn("Target pad not found for edge removal:", fullId);
            continue;
          }
          targetPad.previous_pad = null;

          requests.push({
            type: "edit",
            edit: {
              type: "disconnect_pad",
              node: sourceNodeId,
              pad: sourcePadId,
              connected_node: targetNodeId,
              connected_pad: targetPadId,
            } as DisconnectPadEdit,
          });
        } else if (change.type === "add") {
        }
      }
      if (dirty) {
        setLocalRepresentation({ ...prev });
      }
      for (const req of requests) {
        sendRequest(req);
      }
    },
    [localRepresentation, sendRequest],
  );

  const onReactFlowConnect = useCallback(
    (connection: Connection) => {
      const edit: ConnectPadEdit = {
        type: "connect_pad",
        node: connection.source || "ERROR",
        pad: connection.sourceHandle || "ERROR",
        connected_node: connection.target || "ERROR",
        connected_pad: connection.targetHandle || "ERROR",
      };
      sendRequest({ type: "edit", edit });
    },
    [sendRequest],
  );

  const unsavedChanges = useMemo(() => {
    return JSON.stringify(localRepresentation) !== JSON.stringify(savedGraph);
  }, [localRepresentation, savedGraph]);

  const saveChanges = useCallback(async () => {
    if (saving) {
      console.warn("Already saving changes, ignoring request.");
      return;
    }
    const graph = localRepresentation;
    if (!graph) {
      console.warn("No local representation to save.");
      return;
    }
    setSaving(true);
    try {
      await saveImpl(localRepresentation);
    } catch (error) {
      console.error("Error saving changes:", error);
      toast.error("Failed to save changes. Please try again.");
    } finally {
      setSaving(false);
    }
  }, [localRepresentation, saveImpl, saving]);

  return (
    <EditorContext.Provider
      value={{
        reactFlowRepresentation,
        editorRepresentation: localRepresentation || { nodes: [] },
        isConnected,
        connectionStatus,
        nodeLibrary,
        unsavedChanges,
        saving,
        debug,
        saveChanges,
        onReactFlowConnect,
        onReactFlowNodesChange,
        onReactFlowEdgesChange,
        insertNode,
        insertSubGraph,
        removeNode,
        connectPad,
        updatePad,
        updateNode,
      }}
    >
      {children}
    </EditorContext.Provider>
  );
}

export function useEditor() {
  const context = useContext(EditorContext);
  if (context === undefined) {
    throw new Error("useEditor must be used within a EditorProvider");
  }
  return context;
}

function graphToReact(
  representation: GraphEditorRepresentation,
): ReactFlowRepresentation {
  const nodes: Node[] = representation.nodes.map((node) => ({
    id: node.id,
    type: "default",
    position: {
      x: (node.editor_position?.[0] || 0) as number,
      y: (node.editor_position?.[1] || 0) as number,
    },
    measured: {
      width: (node.editor_dimensions?.[0] || 10) as number,
      height: (node.editor_dimensions?.[1] || 10) as number,
    },
    data: node,
  }));

  const edges: Edge[] = [];
  for (const node of representation.nodes) {
    if (!node.pads) continue;
    for (const pad of node.pads) {
      if (!pad.next_pads) continue;
      for (const connectedPad of pad.next_pads) {
        const edgeId = `${node.id}-${pad.id}-${connectedPad.node}-${connectedPad.pad}`;
        edges.push({
          id: edgeId,
          source: node.id,
          sourceHandle: pad.id,
          target: connectedPad.node,
          targetHandle: connectedPad.pad,
        });
      }
    }
  }

  return { nodes, edges };
}
