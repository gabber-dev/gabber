/**
 * Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
 * SPDX-License-Identifier: SUL-1.0
 */

import { useState, useMemo } from "react";
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
    stateMachineEditing,
    connectionStatus,
    setStateMachineEditing,
    onReactFlowEdgesChange,
    onReactFlowNodesChange,
    onReactFlowConnect,
  } = useEditor();
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

  return (
    <div className="relative w-full h-full flex flex-col">
      <div className="absolute top-2 right-2 flex z-10">
        <AddBlockButton
          onClick={() => setIsNodeLibraryOpen(!isNodeLibraryOpen)}
        />
      </div>

      {/* Node Library Panel */}
      <div
        className={`
          fixed top-[70px] right-0 w-[400px] h-[calc(100vh-70px-64px)] bg-base-300 border-l-2 border-primary overflow-hidden z-20
          transform transition-transform duration-300 ease-in-out
          ${isNodeLibraryOpen ? "translate-x-0" : "translate-x-full"}
        `}
      >
        <NodeLibrary
          setIsModalOpen={setIsNodeLibraryOpen}
          isOpen={isNodeLibraryOpen}
        />
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
            defaultEdgeOptions={{
              type: "hybrid",
              style: { strokeWidth: 2, stroke: "#FCD34D" },
            }}
            proOptions={{
              hideAttribution: true,
            }}
            nodesDraggable={!isRunning}
            nodesConnectable={!isRunning}
            selectNodesOnDrag={false}
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
