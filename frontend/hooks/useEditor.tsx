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
  RemoveNodeEdit,
  Request,
  Response,
  UpdateNodeEdit,
  UpdatePadEdit,
} from "@/generated/editor";
import { Connection, Edge, EdgeChange, Node, NodeChange } from "@xyflow/react";
import React, {
  createContext,
  useContext,
  useState,
  useEffect,
  useCallback,
  useMemo,
} from "react";
import useWebSocket, { ReadyState } from "react-use-websocket";
import toast from "react-hot-toast";

type EditorContextType = {
  editorRepresentation: GraphEditorRepresentation;
  reactFlowRepresentation: Record<string, any>;
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
  toggleDisplayState: (nodeId: string) => void;
};

const EditorContext = createContext<EditorContextType | undefined>(undefined);

type Props = {
  children: React.ReactNode;
  editor_url: string;
  savedGraph: GraphEditorRepresentation;
  saveImpl: (snapshot: GraphEditorRepresentation) => Promise<void>;
};

export function EditorProvider({
  children,
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
  const [selectedNodes, setSelectedNodes] = useState<string[]>([]);
  const [selectedEdges, setSelectedEdges] = useState<string[]>([]);

  const { sendMessage, lastJsonMessage, readyState } = useWebSocket(
    editor_url,
    {
      shouldReconnect: (closeEvent: any) => {
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

  const updatePad = useCallback(
    (edit: UpdatePadEdit) => {
      sendRequest({
        type: "edit",
        edit,
      });
      setLocalRepresentation((prev) => {
        if (!prev) return prev;
        let node = prev.nodes.find((n) => n.id === edit.node);
        if (!node) {
          console.warn(
            `Node with id ${edit.node} not found in local representation`,
          );
          return prev;
        }
        let pad = node.pads.find((p) => p.id === edit.pad);
        if (!pad) {
          console.warn(
            `Pad with id ${edit.pad} not found in node ${edit.node}`,
          );
          return prev;
        }

        pad = { ...pad, value: edit.value };
        node.pads = node.pads.map((p) => (p.id === edit.pad ? pad : p));
        node = { ...node };
        return { ...prev };
      });
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
        setSelectedNodes((prev) =>
          prev.map((nodeId) => (nodeId === edit.id ? edit.new_id! : nodeId)),
        );
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

  const toggleDisplayState = useCallback(
    (nodeId: string) => {
      sendRequest({
        type: "edit",
        edit: {
          type: "toggle_display_state",
          node_id: nodeId,
        },
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

  const reactFlowRepresentation = useMemo(() => {
    if (!localRepresentation)
      return {
        nodes: [],
        edges: [],
      };

    const nodes: Node[] = localRepresentation.nodes.map((node) => ({
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
      selected: selectedNodes.includes(node.id),
    }));

    const edges: Edge[] = [];

    for (const node of localRepresentation.nodes) {
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
            selected: selectedEdges.includes(edgeId),
          });
        }
      }
    }

    return { nodes, edges };
  }, [localRepresentation, selectedEdges, selectedNodes]);

  const onReactFlowNodesChange = useCallback(
    (changes: NodeChange[]) => {
      const prev = localRepresentation;
      let dirty = false;
      if (!prev) {
        console.warn("No previous representation available");
        return;
      }
      const requests: Request[] = [];
      const selectedNodes: string[] = [];
      for (const change of changes) {
        if (change.type === "position") {
          const nodeId = change.id;
          const newPosition = change.position;
          const oldPosition = prev.nodes.find(
            (n) => n.id === nodeId,
          )?.editor_position;
          if (!newPosition || !oldPosition) {
            continue;
          }

          if (!change.dragging) {
            const edit: UpdateNodeEdit = {
              type: "update_node",
              id: nodeId,
              editor_name: null,
              new_id: null,
              editor_position: [newPosition.x, newPosition.y],
              editor_dimensions: null,
            };
            requests.push({ type: "edit", edit });
          }

          if (
            newPosition.x === oldPosition[0] &&
            newPosition.y === oldPosition[1]
          ) {
            continue; // No change in position
          }
          dirty = true;
          for (const node of prev?.nodes || []) {
            if (node.id === nodeId) {
              node.editor_position = [newPosition?.x, newPosition?.y];
            }
          }
        } else if (change.type === "select") {
          if (change.selected) {
            selectedNodes.push(change.id);
          }
        } else if (change.type === "remove") {
          const nodeId = change.id;
          dirty = true;
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
          dirty = true;
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
      setSelectedNodes(selectedNodes);
      if (dirty) {
        setLocalRepresentation({ ...prev });
      }
      for (const req of requests) {
        sendRequest(req);
      }
    },
    [localRepresentation, sendRequest],
  );

  const onReactFlowEdgesChange = useCallback(
    (changes: EdgeChange[]) => {
      const selectedEdges: string[] = [];
      let dirty = false;
      const prev = localRepresentation;
      if (!prev) {
        console.warn("No previous representation available");
        return;
      }
      const requests: Request[] = [];
      for (const change of changes) {
        if (change.type === "select") {
          if (change.selected) {
            selectedEdges.push(change.id);
          }
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
      setSelectedEdges(selectedEdges);
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
        toggleDisplayState,
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
