/**
 * Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
 * SPDX-License-Identifier: SUL-1.0
 */

import { useState, useCallback, useMemo, useEffect } from "react";
import {
  ReactFlow,
  Background,
  BackgroundVariant,
  ReactFlowProvider,
  Node,
  Edge,
  NodeChange,
} from "@xyflow/react";

import "@xyflow/react/dist/base.css";
import { FlowErrorBoundary } from "./ErrorBoundary";
import { useEditor } from "@/hooks/useEditor";
import { BaseBlock } from "./blocks/BaseBlock";
import { XMarkIcon, PlusIcon } from "@heroicons/react/24/outline";
import { NodeLibrary } from "./NodeLibrary";
import { PropertySidebar } from "./PropertySidebar";
import { HybridEdge } from "./edges/HybridEdge";
import { CustomConnectionLine } from "./edges/CustomConnectionLine";

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
    onReactFlowEdgesChange,
    onReactFlowNodesChange: originalOnNodesChange,
    onReactFlowConnect,
  } = useEditor();

  const onReactFlowNodesChange = useCallback(
    (changes: NodeChange[]) => {
      const snappedChanges = changes.map((change: NodeChange) => {
        if (change.type === "position" && !change.dragging && change.position) {
          // Only snap when drag ends
          return {
            ...change,
            position: {
              x: Math.round(change.position.x / 12) * 12,
              y: Math.round(change.position.y / 12) * 12,
            },
          };
        }
        return change;
      });
      originalOnNodesChange(snappedChanges);
    },
    [originalOnNodesChange],
  );

  const [isPropertyPanelOpen, setIsPropertyPanelOpen] = useState(false);
  const { connectionStatus } = useEditor();

  const handlePropertyPanelToggle = useCallback(() => {
    setIsPropertyPanelOpen(!isPropertyPanelOpen);
  }, [isPropertyPanelOpen]);

  const selectedNode = reactFlowRepresentation.nodes.find(
    (node: Node) => node.selected,
  );
  useEffect(() => {
    if (selectedNode && !isPropertyPanelOpen) {
      handlePropertyPanelToggle();
    } else if (!selectedNode && isPropertyPanelOpen) {
      setIsPropertyPanelOpen(false);
    }
  }, [selectedNode, isPropertyPanelOpen, handlePropertyPanelToggle]);

  const styledEdges = useMemo(() => {
    return reactFlowRepresentation.edges.map((edge: Edge) => ({
      ...edge,
      type: "hybrid",
    }));
  }, [reactFlowRepresentation.edges]);

  return (
    <div className="relative w-full h-full flex flex-col">
      <div className="absolute top-2 right-2 flex z-60">
        <AddBlockButton />
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
            nodes={reactFlowRepresentation.nodes as Node[]}
            edges={styledEdges as Edge[]}
            onNodesChange={onReactFlowNodesChange}
            onEdgesChange={onReactFlowEdgesChange}
            onConnect={onReactFlowConnect}
            edgeTypes={edgeTypes}
            connectionLineComponent={CustomConnectionLine}
            fitView
            nodeTypes={{ default: BaseBlock }}
            defaultEdgeOptions={{
              type: "hybrid",
              style: { strokeWidth: 2, stroke: "#FCD34D" },
            }}
            proOptions={{
              hideAttribution: true,
            }}
          >
            <Background variant={BackgroundVariant.Dots} gap={12} size={1} />
          </ReactFlow>
        </FlowErrorBoundary>
      </div>

      {selectedNode && (
        <div className="absolute top-16 right-2 bottom-2 z-10">
          <PropertySidebar onToggle={handlePropertyPanelToggle} />
        </div>
      )}
    </div>
  );
}

function AddBlockButton() {
  const [isModalOpen, setIsModalOpen] = useState(false);

  return (
    <>
      <button
        onClick={() => setIsModalOpen(!isModalOpen)}
        className={`
          btn btn-sm gap-2 font-vt323 tracking-wider
          ${isModalOpen ? "btn-error" : "btn-warning"}
        `}
      >
        {isModalOpen ? (
          <XMarkIcon className="h-4 w-4" />
        ) : (
          <PlusIcon className="h-4 w-4" />
        )}
        {isModalOpen ? "Close" : "Add Node"}
      </button>

      {isModalOpen && (
        <div className="absolute top-12 right-0 w-96 h-[calc(100vh-10rem)] bg-base-300 rounded-lg shadow-xl border-2 border-primary overflow-hidden">
          <NodeLibrary setIsModalOpen={setIsModalOpen} />
        </div>
      )}
    </>
  );
}
