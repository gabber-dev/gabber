/**
 * Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
 * SPDX-License-Identifier: SUL-1.0
 */

import { useState, useMemo, useCallback } from "react";
import {
  ReactFlow,
  Background,
  BackgroundVariant,
  ReactFlowProvider,
  Node,
  Edge,
} from "@xyflow/react";

import "@xyflow/react/dist/base.css";
import { FlowErrorBoundary } from "./ErrorBoundary";
import { useEditor } from "@/hooks/useEditor";
import { useRun } from "@/hooks/useRun";
import { BaseBlock } from "./blocks/BaseBlock";
import { PlusIcon } from "@heroicons/react/24/outline";
import { NodeLibrary } from "./NodeLibrary";

import { HybridEdge } from "./edges/HybridEdge";
import { CustomConnectionLine } from "./edges/CustomConnectionLine";

import { getPrimaryDataType } from "./blocks/components/pads/utils/dataTypeColors";
import ReactModal from "react-modal";
import { StateMachineGraphEdit } from "../state_machine/StateMachineGraphEdit";
import { StateMachineProvider } from "../state_machine/useStateMachine";
import {
  GraphEditorRepresentation,
  NodeEditorRepresentation,
  PadEditorRepresentation,
  PadReference,
} from "@/generated/editor";
import { useRepository } from "@/hooks/useRepository";
import toast from "react-hot-toast";

const edgeTypes = {
  hybrid: HybridEdge,
};

export function FlowEdit() {
  return (
    <ReactFlowProvider>
      <FlowErrorBoundary>
        <FlowEditInner />
      </FlowErrorBoundary>
    </ReactFlowProvider>
  );
}

function FlowEditInner() {
  const {
    reactFlowRepresentation,
    editorRepresentation,
    stateMachineEditing,
    connectionStatus,
    setStateMachineEditing,
    onReactFlowEdgesChange,
    onReactFlowNodesChange,
    onReactFlowConnect,
    // no inline insertion for now
  } = useEditor();
  const { saveSubGraph } = useRepository();
  const { connectionState } = useRun();
  const isRunning =
    connectionState === "connected" || connectionState === "connecting";

  const [isNodeLibraryOpen, setIsNodeLibraryOpen] = useState(false);

  const styledEdges = useMemo(() => {
    return reactFlowRepresentation.edges.map((edge: Edge) => {
      const sourceNode = reactFlowRepresentation.nodes.find(
        (node: Node) => node.id === edge.source,
      );
      const sourcePad = sourceNode?.data.pads.find(
        (pad) => pad.id === edge.sourceHandle,
      );
      const dataType = getPrimaryDataType(sourcePad?.allowed_types || []);
      return {
        ...edge,
        type: "hybrid",
        data: {
          ...edge.data,
          dataType,
        },
      };
    });
  }, [reactFlowRepresentation.edges, reactFlowRepresentation.nodes]);

  const selectedNodeIds = useMemo(() => {
    return new Set(
      (reactFlowRepresentation.nodes as Node[])
        .filter((n) => Boolean((n as any).selected))
        .map((n) => n.id),
    );
  }, [reactFlowRepresentation.nodes]);

  const onCreateSubgraphFromSelection = useCallback(async () => {
    if (selectedNodeIds.size === 0) return;

    // Ask for a name for the new subgraph
    const name = window.prompt("Name your new subgraph:", "New SubGraph");
    if (!name) return;

    const snapshot = buildSubgraphSnapshot(
      editorRepresentation,
      selectedNodeIds,
    );

    // Save to repository only (no graph mutation for now)
    const saved = await saveSubGraph({ name, graph: snapshot } as any);

    toast.custom((t) => (
      <div className="flex items-start gap-3 bg-base-200 border border-base-300 rounded-lg px-4 py-3 shadow-xl">
        <div className="text-sm">
          <div className="font-semibold">Subgraph saved</div>
          <a
            href={`/graph/${saved.id}`}
            className="link link-primary underline"
            onClick={() => toast.dismiss(t.id)}
          >
            Open subgraph
          </a>
        </div>
        <button
          className="btn btn-xs btn-ghost ml-2"
          onClick={() => toast.dismiss(t.id)}
        >
          Close
        </button>
      </div>
    ));
  }, [editorRepresentation, saveSubGraph, selectedNodeIds]);

  return (
    <div className="relative w-full h-full flex flex-col">
      <div className="absolute top-2 right-2 flex z-10">
        <AddBlockButton
          onClick={() => setIsNodeLibraryOpen(!isNodeLibraryOpen)}
        />
        {selectedNodeIds.size > 0 && (
          <button
            className="btn btn-sm ml-2 font-vt323 tracking-wider btn-accent"
            onClick={onCreateSubgraphFromSelection}
          >
            Save as Subgraph
          </button>
        )}
      </div>

      {/* Node Library Panel */}
      <div
        className={`
          fixed top-[70px] right-0 w-[400px] h-[calc(100vh-70px-64px)] bg-base-300 border-l-2 border-primary overflow-hidden z-20
          transform transition-transform duration-300 ease-in-out
          ${isNodeLibraryOpen ? "translate-x-0" : "translate-x-full"}
        `}
      >
        <NodeLibrary setIsModalOpen={setIsNodeLibraryOpen} />
      </div>

      {connectionStatus && (
        <div className="absolute top-[3.25rem] right-2 z-0 text-xs text-success pointer-events-none">
          {connectionStatus}
        </div>
      )}

      <div
        className={`absolute top-0 left-0 right-0 bottom-0 transition-all duration-300 ease-in-out`}
      >
        <FlowErrorBoundary>
          <ReactFlow
            className=""
            nodes={reactFlowRepresentation.nodes as Node[]}
            edges={styledEdges as Edge[]}
            onNodesChange={(changes) => {
              // Close node library if a node is selected
              const selectionChange = changes.find(
                (change) => change.type === "select",
              );
              if (selectionChange?.selected && isNodeLibraryOpen) {
                setIsNodeLibraryOpen(false);
              }
              onReactFlowNodesChange(changes);
            }}
            onEdgesChange={onReactFlowEdgesChange}
            onConnect={onReactFlowConnect}
            edgeTypes={edgeTypes}
            connectionLineComponent={CustomConnectionLine}
            fitView
            nodeTypes={{ default: BaseBlock }}
            snapGrid={[12, 12]}
            snapToGrid={true}
            selectionOnDrag={true}
            defaultEdgeOptions={{
              type: "hybrid",
              style: { strokeWidth: 2, stroke: "#FCD34D" },
            }}
            proOptions={{
              hideAttribution: true,
            }}
            nodesDraggable={!isRunning}
            nodesConnectable={!isRunning}
          >
            <Background variant={BackgroundVariant.Dots} gap={12} size={1} />
          </ReactFlow>
        </FlowErrorBoundary>
      </div>
      
      <ReactModal
        isOpen={Boolean(stateMachineEditing)}
        onRequestClose={() => setStateMachineEditing(undefined)}
        overlayClassName="fixed top-0 bottom-0 left-0 right-0 backdrop-blur-lg bg-blur flex justify-center items-center z-11"
        shouldCloseOnOverlayClick={true}
      >
        <StateMachineProvider nodeId={stateMachineEditing || ""}>
          <div className="fixed top-10 left-10 right-10 bottom-10 flex justify-center items-center border border-purple-500 border-2 rounded-lg overflow-hidden bg-base-100">
            <button
              className="btn bg-purple-500 text-white absolute top-2 right-2 z-10"
              onClick={() => setStateMachineEditing(undefined)}
            >
              Close
            </button>
            <StateMachineGraphEdit />
          </div>
        </StateMachineProvider>
      </ReactModal>
    </div>
  );
}

function AddBlockButton({ onClick }: { onClick: () => void }) {
  return (
    <button
      onClick={onClick}
      className="btn btn-sm gap-2 font-vt323 tracking-wider btn-warning"
    >
      <PlusIcon className="h-4 w-4" />
      Add Node
    </button>
  );
}

function buildSubgraphSnapshot(
  graph: GraphEditorRepresentation,
  selected: Set<string>,
): GraphEditorRepresentation {
  const selectedSet = new Set<string>(selected);

  // Start with a deep-ish copy of selected nodes
  const innerNodes: NodeEditorRepresentation[] = graph.nodes
    .filter((n) => selectedSet.has(n.id))
    .map((orig) => ({
      ...orig,
      pads: orig.pads.map((p) => ({
        ...p,
        next_pads: [...(p.next_pads || [])],
        previous_pad: p.previous_pad ? { ...p.previous_pad } : undefined,
      })),
    }));

  // Container for proxy nodes we add inside the subgraph snapshot
  const proxyNodes: NodeEditorRepresentation[] = [];

  function ensureInboundProxy(
    targetNode: NodeEditorRepresentation,
    targetPadId: string,
    padType: string,
    allowedTypes?: any[] | null,
  ): NodeEditorRepresentation {
    const proxyId = `proxy_in_${targetNode.id}_${targetPadId}`;
    let n = proxyNodes.find((x) => x.id === proxyId);
    if (n) return n;

    const isProperty = padType === "PropertySinkPad";
    n = {
      id: proxyId,
      type: isProperty ? "ProxyPropertySink" : "ProxyStatelessSink",
      editor_name: proxyId,
      editor_position: [
        ((targetNode.editor_position?.[0] || 0) as number) - 200,
        (targetNode.editor_position?.[1] || 0) as number,
      ],
      editor_dimensions: null,
      metadata: { primary: "subgraph", secondary: "proxy", tags: [] },
      description: "",
      pads: [
        {
          id: "proxy",
          group: "proxy",
          type: isProperty ? "PropertySourcePad" : "StatelessSourcePad",
          next_pads: [],
          ...(allowedTypes ? { allowed_types: allowedTypes as any } : {}),
        } as unknown as PadEditorRepresentation,
        {
          id: "pad_id",
          group: "pad_id",
          type: "PropertySinkPad",
          value: `proxy_${proxyId}`,
          next_pads: [],
          allowed_types: [{ type: "string" }] as any,
        } as unknown as PadEditorRepresentation,
      ],
    };
    proxyNodes.push(n);
    return n;
  }

  function ensureOutboundProxy(
    sourceNode: NodeEditorRepresentation,
    sourcePadId: string,
    padType: string,
    allowedTypes?: any[] | null,
  ): NodeEditorRepresentation {
    const proxyId = `proxy_out_${sourceNode.id}_${sourcePadId}`;
    let n = proxyNodes.find((x) => x.id === proxyId);
    if (n) return n;

    const isProperty = padType === "PropertySourcePad";
    const width = ((sourceNode.editor_dimensions?.[0] || 160) as number);
    n = {
      id: proxyId,
      type: isProperty ? "ProxyPropertySource" : "ProxyStatelessSource",
      editor_name: proxyId,
      editor_position: [
        ((sourceNode.editor_position?.[0] || 0) as number) + width + 40,
        (sourceNode.editor_position?.[1] || 0) as number,
      ],
      editor_dimensions: null,
      metadata: { primary: "subgraph", secondary: "proxy", tags: [] },
      description: "",
      pads: [
        {
          id: "proxy",
          group: "proxy",
          type: isProperty ? "PropertySinkPad" : "StatelessSinkPad",
          next_pads: [],
          ...(allowedTypes ? { allowed_types: allowedTypes as any } : {}),
        } as unknown as PadEditorRepresentation,
        {
          id: "pad_id",
          group: "pad_id",
          type: "PropertySinkPad",
          value: `proxy_${proxyId}`,
          next_pads: [],
          allowed_types: [{ type: "string" }] as any,
        } as unknown as PadEditorRepresentation,
      ],
    };
    proxyNodes.push(n);
    return n;
  }

  // Traverse all edges using next_pads (source side)
  for (const node of graph.nodes) {
    for (const pad of node.pads) {
      const nexts = pad.next_pads || [];
      for (const np of nexts) {
        const srcNodeId = node.id;
        const srcPadId = pad.id;
        const dstNodeId = np.node;
        const dstPadId = np.pad;

        const srcInSel = selectedSet.has(srcNodeId);
        const dstInSel = selectedSet.has(dstNodeId);

        if (srcInSel && dstInSel) {
          // Internal edge – nothing to do
          continue;
        }

        if (!srcInSel && dstInSel) {
          // Inbound edge (external -> selected sink). Add Proxy*Sink and hook it to target sink.
          const targetNode = innerNodes.find((n) => n.id === dstNodeId)!;
          const targetPad = targetNode.pads.find((p) => p.id === dstPadId)!;
          // Clear external previous_pad (will be fed by proxy source)
          (targetPad as any).previous_pad = undefined;

          const proxy = ensureInboundProxy(
            targetNode,
            dstPadId,
            (targetPad as any).type,
            (targetPad as any).allowed_types || null,
          );
          const proxySource = proxy.pads.find(
            (p) => p.type === "StatelessSourcePad" || p.type === "PropertySourcePad",
          )! as PadEditorRepresentation;
          proxySource.next_pads = [
            { node: targetNode.id, pad: targetPad.id } as unknown as PadReference,
          ];
          // Also mark target's previous to point to proxy so UI engines that read both sides show edge
          (targetPad as any).previous_pad = {
            node: proxy.id,
            pad: proxySource.id,
          } as unknown as PadReference;
        } else if (srcInSel && !dstInSel) {
          // Outbound edge (selected source -> external). Add Proxy*Source and hook it to source.
          const sourceNode = innerNodes.find((n) => n.id === srcNodeId)!;
          const sourcePad = sourceNode.pads.find((p) => p.id === srcPadId)!;

          // Remove external next reference in snapshot
          sourcePad.next_pads = (sourcePad.next_pads || []).filter(
            (p) => !(p.node === dstNodeId && p.pad === dstPadId),
          );

          const proxy = ensureOutboundProxy(
            sourceNode,
            srcPadId,
            (sourcePad as any).type,
            (sourcePad as any).allowed_types || null,
          );
          const proxySink = proxy.pads.find(
            (p) => p.type === "StatelessSinkPad" || p.type === "PropertySinkPad",
          )! as PadEditorRepresentation;
          (proxySink as any).previous_pad = {
            node: sourceNode.id,
            pad: sourcePad.id,
          } as unknown as PadReference;

          // Also add a forward edge from source to proxy so the editor renders the connection
          sourcePad.next_pads = [
            ...(sourcePad.next_pads || []),
            { node: proxy.id, pad: proxySink.id } as unknown as PadReference,
          ];
        }
      }
    }
  }

  return { nodes: [...innerNodes, ...proxyNodes] };
}
