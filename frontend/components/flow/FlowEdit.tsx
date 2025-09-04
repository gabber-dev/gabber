/**
 * Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
 * SPDX-License-Identifier: SUL-1.0
 */

import { useState, useCallback } from "react";
import {
  ReactFlow,
  Background,
  BackgroundVariant,
  ReactFlowProvider,
  useReactFlow,
  FinalConnectionState,
} from "@xyflow/react";

import "@xyflow/react/dist/base.css";
import { FlowErrorBoundary } from "./ErrorBoundary";
import { useEditor } from "@/hooks/useEditor";
import { useRun } from "@/hooks/useRun";
import { BaseBlock } from "./blocks/BaseBlock";
import { PlusIcon, ShareIcon } from "@heroicons/react/24/outline";
import { NodeLibrary } from "./NodeLibrary";

import { HybridEdge } from "./edges/HybridEdge";
import { CustomConnectionLine } from "./edges/CustomConnectionLine";

import ReactModal from "react-modal";
import { StateMachineGraphEdit } from "../state_machine/StateMachineGraphEdit";
import { StateMachineProvider } from "../state_machine/useStateMachine";
import { usePathname } from "next/navigation";
import toast from "react-hot-toast";
import { exportApp } from "@/lib/repository";
import { QuickAddModal } from "./quick_add/QuickAddModal";
import { PortalStart } from "./blocks/PortalStart";
import { PortalEnd } from "./blocks/PortalEnd";

const edgeTypes = {
  hybrid: HybridEdge,
};

type Props = {
  editable: boolean;
};

export function FlowEdit(props: Props) {
  return (
    <ReactFlowProvider>
      <FlowErrorBoundary>
        <FlowEditInner {...props} />
      </FlowErrorBoundary>
    </ReactFlowProvider>
  );
}

function FlowEditInner({ editable }: Props) {
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
  const { screenToFlowPosition } = useReactFlow();
  const [quickAdd, setQuickAdd] = useState<
    | {
        source_node: string;
        source_pad: string;
        add_position: { x: number; y: number };
      }
    | undefined
  >(undefined);

  const [isNodeLibraryOpen, setIsNodeLibraryOpen] = useState(false);

  const onConnectEnd = useCallback(
    (event: MouseEvent | TouchEvent, connectionState: FinalConnectionState) => {
      if (!connectionState.isValid) {
        const { clientX, clientY } =
          "changedTouches" in event ? event.changedTouches[0] : event;
        const position = screenToFlowPosition({
          x: clientX,
          y: clientY,
        });
        setQuickAdd({
          source_node: connectionState.fromNode?.id || "",
          source_pad: connectionState.fromHandle?.id || "",
          add_position: position,
        });
      }
    },
    [screenToFlowPosition],
  );

  return (
    <div className="relative w-full h-full flex flex-col">
      <div ref={(el) => ReactModal.setAppElement(el as HTMLDivElement)} />
      {editable && (
        <div className="absolute top-2 right-2 flex z-10 gap-2">
          <ExportButton />
          <AddBlockButton
            onClick={() => setIsNodeLibraryOpen(!isNodeLibraryOpen)}
          />
        </div>
      )}

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
            nodes={reactFlowRepresentation.nodes}
            edges={reactFlowRepresentation.edges}
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
            onConnectEnd={onConnectEnd}
            edgeTypes={edgeTypes}
            connectionLineComponent={CustomConnectionLine}
            fitView
            nodeTypes={{
              node: BaseBlock,
              portal_start: PortalStart,
              portal_end: PortalEnd,
            }}
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
            minZoom={0.1}
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
      <ReactModal
        isOpen={Boolean(quickAdd)}
        onRequestClose={() => setQuickAdd(undefined)}
        overlayClassName="fixed top-0 bottom-0 left-0 right-0 backdrop-blur-xs bg-blur flex justify-center items-center z-11"
        className="bg-base-200 rounded-lg overflow-hidden shadow-lg outline-none h-2/3 w-100"
        shouldCloseOnOverlayClick={true}
      >
        <QuickAddModal
          sourceNode={quickAdd?.source_node || ""}
          sourcePad={quickAdd?.source_pad || ""}
          addPosition={quickAdd?.add_position || { x: 0, y: 0 }}
          close={() => {
            setQuickAdd(undefined);
          }}
        />
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

function ExportButton() {
  const path = usePathname();
  const appId = path.split("/app/")[1];

  const onClick = useCallback(async () => {
    try {
      const { export: appExport } = await exportApp(appId);
      const blob = new Blob([JSON.stringify(appExport, null, 2)], {
        type: "application/json",
      });
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = `${appExport.app.name || "app"}.json`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
    } catch (error) {
      console.error("Error exporting app", error);
      toast.error("Error exporting app");
    }
    console.log("Exporting", appId, path);
  }, [appId, path]);

  if (!path.startsWith("/app/")) {
    return null;
  }

  return (
    <button
      onClick={onClick}
      className="btn btn-sm gap-2 font-vt323 tracking-wider btn-primary"
    >
      <ShareIcon className="h-4 w-4" />
    </button>
  );
}
