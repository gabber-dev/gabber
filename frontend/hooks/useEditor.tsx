/**
 * Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
 * SPDX-License-Identifier: SUL-1.0
 */

"use client";

import {
  ConnectPadEdit,
  CreatePortalEdit,
  CreatePortalEndEdit,
  DeletePortalEdit,
  DeletePortalEndEdit,
  Edit,
  EditRequest,
  EligibleLibraryItem,
  GraphEditorRepresentation,
  GraphLibraryItem_Node,
  GraphLibraryItem_SubGraph,
  InsertNodeEdit,
  InsertSubGraphEdit,
  NodeEditorRepresentation,
  PadEditorRepresentation,
  Portal,
  PortalEnd,
  QueryEligibleNodeLibraryItemsRequest,
  RemoveNodeEdit,
  Request,
  Response,
  UpdateNodeEdit,
  UpdatePadEdit,
  UpdatePortalEdit,
  UpdatePortalEndEdit,
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
import { v4 } from "uuid";
import {
  getDataTypeColor,
  getPrimaryDataType,
} from "@/components/flow/blocks/components/pads/utils/dataTypeColors";

type ReactFlowRepresentation = {
  nodes: Node[];
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
  stateMachineEditing?: string;
  setStateMachineEditing: (stateMachineId: string | undefined) => void;
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

  createPortal: (req: CreatePortalEdit) => void;
  createPortalEnd: (req: CreatePortalEndEdit) => void;
  deletePortal: (req: DeletePortalEdit) => void;
  deletePortalEnd: (req: DeletePortalEndEdit) => void;
  updatePortal: (req: UpdatePortalEdit) => void;
  updatePortalEnd: (req: UpdatePortalEndEdit) => void;

  queryEligibleLibraryItems: ({
    sourceNode,
    sourcePad,
  }: {
    sourceNode: string;
    sourcePad: string;
  }) => Promise<EligibleLibraryItem[]>;
  clearAllSelection: () => void;
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
  const [stateMachineEditing, setStateMachineEditing] = useState<
    string | undefined
  >(undefined);

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

  const pendingRequests = useRef<
    Map<
      string,
      {
        resolve: (value: Response) => void;
        reject: (reason?: Error) => void;
        timeoutId: number;
      }
    >
  >(new Map());

  const reactFlowRef = useRef(reactFlowRepresentation);

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

  useEffect(() => {
    if (readyState === ReadyState.CLOSED) {
      for (const [, pending] of pendingRequests.current.entries()) {
        clearTimeout(pending.timeoutId);
        pending.reject(new Error("WebSocket connection closed"));
      }
      pendingRequests.current.clear();
    }
  }, [readyState]);

  const sendRequest = useCallback(
    (request: Request) => {
      if (!isConnected) {
        console.error("NEIL not connected", request);
        console.warn("WebSocket is not connected. Cannot send request.");
        return Promise.reject(new Error("WebSocket not connected"));
      }
      if (!request.req_id) {
        request.req_id = v4();
      }
      const req_id = request.req_id;
      sendMessage(JSON.stringify(request));
      return new Promise<Response>((resolve, reject) => {
        const timeoutId = setTimeout(() => {
          pendingRequests.current.delete(req_id);
          reject(new Error("Request timed out after 5 seconds"));
        }, 5000) as unknown as number;
        pendingRequests.current.set(req_id, { resolve, reject, timeoutId });
      });
    },
    [isConnected, sendMessage],
  );

  const insertNode = useCallback(
    (edit: InsertNodeEdit) => {
      sendRequest({
        type: "edit",
        edits: [edit],
        req_id: v4(),
      });
    },
    [sendRequest],
  );

  const insertSubGraph = useCallback(
    (edit: InsertSubGraphEdit) => {
      sendRequest({
        type: "edit",
        edits: [edit],
        req_id: v4(),
      });
    },
    [sendRequest],
  );

  const removeNode = useCallback(
    (edit: RemoveNodeEdit) => {
      sendRequest({
        type: "edit",
        edits: [edit],
        req_id: v4(),
      });
    },
    [sendRequest],
  );

  const connectPad = useCallback(
    (edit: ConnectPadEdit) => {
      sendRequest({
        type: "edit",
        edits: [edit],
        req_id: v4(),
      });
    },
    [sendRequest],
  );

  const createPortal = useCallback(
    (edit: CreatePortalEdit) => {
      sendRequest({
        type: "edit",
        edits: [edit],
        req_id: v4(),
      });
    },
    [sendRequest],
  );

  const createPortalEnd = useCallback(
    (edit: CreatePortalEndEdit) => {
      sendRequest({
        type: "edit",
        edits: [edit],
        req_id: v4(),
      });
    },
    [sendRequest],
  );

  const updatePortal = useCallback(
    (edit: UpdatePortalEdit) => {
      sendRequest({
        type: "edit",
        edits: [edit],
        req_id: v4(),
      });
    },
    [sendRequest],
  );

  const updatePortalEnd = useCallback(
    (edit: UpdatePortalEndEdit) => {
      sendRequest({
        type: "edit",
        edits: [edit],
        req_id: v4(),
      });
    },
    [sendRequest],
  );

  const deletePortal = useCallback(
    (edit: DeletePortalEdit) => {
      sendRequest({
        type: "edit",
        edits: [edit],
        req_id: v4(),
      });
    },
    [sendRequest],
  );

  const deletePortalEnd = useCallback(
    (edit: DeletePortalEndEdit) => {
      sendRequest({
        type: "edit",
        edits: [edit],
        req_id: v4(),
      });
    },
    [sendRequest],
  );

  const queryEligibleLibraryItems = useCallback(
    async (params: { sourceNode: string; sourcePad: string }) => {
      const req: QueryEligibleNodeLibraryItemsRequest = {
        source_node: params.sourceNode,
        source_pad: params.sourcePad,
        req_id: v4(),
        type: "query_eligible_node_library_items",
      };
      const resp = await sendRequest(req);
      return resp.direct_eligible_items as EligibleLibraryItem[];
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
            edits: [pendingEdit],
            req_id: v4(),
          });
          pendingEdits.current.delete(key);
        }
        debounceTimers.current.delete(key);
      }, 250) as unknown as number;

      debounceTimers.current.set(key, timer);
    },
    [sendRequest],
  );

  const clearAllSelection = useCallback(() => {
    setReactFlowRepresentation((prev) => {
      return {
        ...prev,
        nodes: prev.nodes.map((node) => ({
          ...node,
          selected: false,
        })),
        edges: prev.edges.map((edge) => ({
          ...edge,
          selected: false,
        })),
      };
    });
  }, []);

  const updateNode = useCallback(
    (edit: UpdateNodeEdit) => {
      sendRequest({
        type: "edit",
        edits: [edit],
        req_id: v4(),
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
        req_id: v4(),
      });

      sendRequest({ type: "get_node_library", req_id: v4() });
    }
  }, [localRepresentation, prevReadyState, readyState, sendRequest]);

  useEffect(() => {
    if (!lastJsonMessage) return;

    try {
      const resp = lastJsonMessage as Response;
      const req_id = resp.req_id || "";

      if (resp.type === "node_library") {
        setNodeLibrary(resp.node_library || []);
      } else if (resp.type === "load_from_snapshot") {
        setLocalRepresentation(resp.graph);
      } else if (resp.type === "edit") {
        setLocalRepresentation(resp.graph);
      } else if (resp.type === "query_eligible_node_library_items") {
        // No global state update needed for per-query responses
      }

      const pending = pendingRequests.current.get(req_id);
      console.log("NEIL pending request", pending, req_id, resp);
      if (pending) {
        clearTimeout(pending.timeoutId);
        pendingRequests.current.delete(req_id);
        pending.resolve(resp);
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
      const edits: Edit[] = [];
      for (const change of changes) {
        if (change.type === "position") {
          reactFlowRepresentation.nodes = applyNodeChanges(
            [change],
            reactFlowRepresentation.nodes,
          );

          if (!change.dragging) {
            const node = prev.nodes.find((n) => n.id === change.id);

            if (node) {
              edits.push({
                type: "update_node",
                id: change.id,
                editor_name: null,
                new_id: null,
                editor_position: [change.position?.x, change.position?.y],
                editor_dimensions: null,
              });
            } else {
              const portalStart = (prev.portals || []).find(
                (p) => p.id === change.id,
              );
              if (portalStart) {
                edits.push({
                  type: "update_portal",
                  portal_id: change.id,
                  editor_position: [change.position?.x, change.position?.y],
                });
              } else {
                let portalEnd: PortalEnd | undefined;
                let portalStart: Portal | undefined;
                for (const p of prev.portals || []) {
                  for (const pe of p.ends || []) {
                    if (pe.id === change.id) {
                      portalStart = p;
                      portalEnd = pe;
                      break;
                    }
                  }
                }
                if (portalEnd && portalStart) {
                  edits.push({
                    type: "update_portal_end",
                    portal_id: portalStart.id,
                    portal_end_id: portalEnd.id,
                    editor_position: [change.position?.x, change.position?.y],
                    next_pads: portalEnd.next_pads,
                  });
                }
              }
            }
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
          edits.push({
            type: "remove_node",
            node_id: nodeId,
          });
          prev.nodes = prev.nodes.filter((n) => n.id !== nodeId);
        } else if (change.type === "add") {
        } else if (change.type === "dimensions") {
          // Handle node dimension changes
          const nodeId = change.id;
          const node = prev.nodes.find((n) => n.id === nodeId);
          if (!node) {
            continue;
          }
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
          edits.push(edit);
          for (const node of prev?.nodes || []) {
            if (node.id === nodeId) {
              node.editor_dimensions = [newDims?.width, newDims?.height];
            }
          }
        }
      }
      if (edits.length > 0) {
        const req: EditRequest = {
          type: "edit",
          edits,
          req_id: v4(),
        };
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
      const edits: Edit[] = [];
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

          edits.push({
            type: "disconnect_pad",
            node: sourceNodeId,
            pad: sourcePadId,
            connected_node: targetNodeId,
            connected_pad: targetPadId,
          });
        } else if (change.type === "add") {
        }
      }
      if (dirty) {
        setLocalRepresentation({ ...prev });
      }
      for (const e of edits) {
        sendRequest({ type: "edit", edits: [e], req_id: v4() });
      }
    },
    [localRepresentation, sendRequest],
  );

  const onReactFlowConnect = useCallback(
    (connection: Connection) => {
      const { nodes } = reactFlowRepresentation;
      const sourceRfNode = nodes.find((n) => n.id === connection.source);
      if (sourceRfNode?.type === "portal_end") {
        const sourcePortalId = sourceRfNode.data.sourcePortalId as string;
        const portalEnd = sourceRfNode.data.portalEnd as PortalEnd;
        const sourceNode = sourceRfNode.data
          .sourceNode as NodeEditorRepresentation;
        const sourcePad = sourceRfNode.data
          .sourcePad as PadEditorRepresentation;

        const connectEdit: ConnectPadEdit = {
          type: "connect_pad",
          node: sourceNode?.id || "ERROR",
          pad: sourcePad?.id || "ERROR",
          connected_node: connection.target || "ERROR",
          connected_pad: connection.targetHandle || "ERROR",
        };
        const portalEndEdit: UpdatePortalEndEdit = {
          type: "update_portal_end",
          portal_id: sourcePortalId,
          portal_end_id: portalEnd.id,
          next_pads: [
            ...(portalEnd.next_pads || []),
            {
              node: connection.target || "ERROR",
              pad: connection.targetHandle || "ERROR",
            },
          ],
          editor_position: portalEnd.editor_position,
        };
        sendRequest({
          type: "edit",
          edits: [connectEdit, portalEndEdit],
          req_id: v4(),
        });
        console.log("Connection from portal_end not supported");
        return;
      }
      const edit: ConnectPadEdit = {
        type: "connect_pad",
        node: connection.source || "ERROR",
        pad: connection.sourceHandle || "ERROR",
        connected_node: connection.target || "ERROR",
        connected_pad: connection.targetHandle || "ERROR",
      };
      sendRequest({ type: "edit", edits: [edit], req_id: v4() });
    },
    [reactFlowRepresentation, sendRequest],
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
        stateMachineEditing,
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
        createPortal,
        createPortalEnd,
        deletePortal,
        deletePortalEnd,
        updatePortal,
        updatePortalEnd,
        clearAllSelection,
        setStateMachineEditing,
        queryEligibleLibraryItems,
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
  const nodeLookup = new Map<string, NodeEditorRepresentation>();
  const nodes: Node[] = [];
  for (const node of representation.nodes) {
    const rfNode: Node = {
      id: node.id,
      type: "node",
      position: {
        x: (node.editor_position?.[0] || 0) as number,
        y: (node.editor_position?.[1] || 0) as number,
      },
      measured: {
        width: (node.editor_dimensions?.[0] || 10) as number,
        height: (node.editor_dimensions?.[1] || 10) as number,
      },
      data: node,
    };
    nodes.push(rfNode);
    nodeLookup.set(node.id, node);
  }

  const portalStarts: Node[] = [];
  const portalEnds: Node[] = [];
  const skipEdges = new Set<string>();
  for (const portal of representation.portals || []) {
    const sourceNode = nodeLookup.get(portal.source_node || "");
    const sourcePad = sourceNode?.pads?.find((p) => p.id === portal.source_pad);
    const dataColor = getDataTypeColor(
      getPrimaryDataType(sourcePad?.allowed_types || []) || "default",
    );
    const startNode = {
      id: portal.id,
      type: "portal_start",
      position: {
        x: (portal.editor_position?.[0] || 0) as number,
        y: (portal.editor_position?.[1] || 0) as number,
      },
      measured: {
        width: 150,
        height: 40,
      },
      data: {
        portal,
        sourcePad,
        dataColor,
      },
    };
    portalStarts.push(startNode);

    console.log("NEIL portal", portal, sourceNode, sourcePad);

    for (const pe of portal.ends || []) {
      for (const np of pe.next_pads || []) {
        const edgeId = `${sourceNode?.id || "ERROR"}-${
          sourcePad?.id || "ERROR"
        }-${np.node}-${np.pad}`;
        skipEdges.add(edgeId);
      }
      portalEnds.push({
        id: pe.id,
        type: "portal_end",
        position: {
          x: (pe.editor_position?.[0] || 0) as number,
          y: (pe.editor_position?.[1] || 0) as number,
        },
        measured: {
          width: 150,
          height: 40,
        },
        data: {
          portalEnd: pe,
          sourcePortalId: portal.id,
          sourceNode,
          sourcePad,
          dataColor,
        },
      });
    }
  }

  console.log("NEIL skipEdges", skipEdges);

  const edges: Edge[] = [];
  for (const node of representation.nodes) {
    if (!node.pads) continue;
    for (const pad of node.pads) {
      if (!pad.next_pads) continue;
      for (const connectedPad of pad.next_pads) {
        if (
          skipEdges.has(
            `${node.id}-${pad.id}-${connectedPad.node}-${connectedPad.pad}`,
          )
        ) {
          continue;
        }
        const edgeId = `${node.id}-${pad.id}-${connectedPad.node}-${connectedPad.pad}`;
        edges.push({
          id: edgeId,
          source: node.id,
          sourceHandle: pad.id,
          target: connectedPad.node,
          targetHandle: connectedPad.pad,
          data: {
            dataType: getPrimaryDataType(pad.allowed_types || []),
          },
        });
      }
    }
  }

  for (const portal of representation.portals || []) {
    const sourceNode = nodeLookup.get(portal.source_node || "");
    const sourcePad = sourceNode?.pads?.find((p) => p.id === portal.source_pad);
    if (!sourceNode || !sourcePad) continue;
    edges.push({
      id: `${sourceNode.id}-${sourcePad.id}-${portal.id}-${portal.id}`,
      source: sourceNode.id,
      sourceHandle: sourcePad.id,
      target: portal.id,
      targetHandle: "target",
      data: {
        dataType: getPrimaryDataType(sourcePad.allowed_types || []),
      },
    });
    for (const pe of portal.ends || []) {
      for (const np of pe.next_pads || []) {
        const targetNode = nodeLookup.get(np.node);
        const targetPad = targetNode?.pads?.find((p) => p.id === np.pad);
        if (!targetNode || !targetPad) continue;
        const edgeId = `${sourceNode.id}-${sourcePad.id}-${targetNode.id}-${targetPad.id}`;
        edges.push({
          id: edgeId,
          source: pe.id,
          sourceHandle: "source",
          target: targetNode.id,
          targetHandle: targetPad.id,
          data: {
            dataType: getPrimaryDataType(sourcePad.allowed_types || []),
          },
        });
      }
    }
  }

  const allNodes = [...nodes, ...portalStarts, ...portalEnds];

  return { nodes: allNodes, edges };
}
