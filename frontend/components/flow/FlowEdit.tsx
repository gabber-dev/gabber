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
import { PlusIcon, ArrowUpTrayIcon } from "@heroicons/react/24/outline";
import { NodeLibrary } from "./NodeLibrary";

import { HybridEdge } from "./edges/HybridEdge";
import { CustomConnectionLine } from "./edges/CustomConnectionLine";

import ReactModal from "react-modal";
import { StateMachineGraphEdit } from "../state_machine/StateMachineGraphEdit";
import { StateMachineProvider } from "../state_machine/useStateMachine";
import { usePathname } from "next/navigation";
import toast from "react-hot-toast";
import { QuickAddModal, QuickAddProps } from "./quick_add/QuickAddModal";

// Throttling for all drag-related warnings (2 seconds for drag operations)
let lastDragWarningTime = 0;
const DRAG_WARNING_THROTTLE_MS = 2000; // 2 seconds for drag operations (matches global)

const showDragWarningThrottled = (message: string) => {
  const now = Date.now();
  if (now - lastDragWarningTime > DRAG_WARNING_THROTTLE_MS) {
    toast.error(message);
    lastDragWarningTime = now;
  }
};
import { PortalStart } from "./blocks/PortalStart";
import { PortalEnd as PortalEndComponent } from "./blocks/PortalEnd";
import {
  NodeEditorRepresentation,
  PadEditorRepresentation,
  PortalEnd,
} from "@/generated/editor";
import { RunId } from "../RunId";
import { useRepository } from "@/hooks/useRepository";

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
  const [quickAdd, setQuickAdd] = useState<QuickAddProps | undefined>(
    undefined,
  );

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
        if (
          connectionState.fromNode?.type === "node" &&
          connectionState.fromHandle?.type === "source"
        ) {
          setQuickAdd({
            sourceNode: connectionState.fromNode?.id || "",
            sourcePad: connectionState.fromHandle?.id || "",
            addPosition: position,
            close: () => setQuickAdd(undefined),
          });
        } else if (connectionState.fromNode?.type === "portal_end") {
          const { data } = connectionState.fromNode || {};
          const { sourceNode, sourcePad } = data || {};
          setQuickAdd({
            sourceNode: (sourceNode as NodeEditorRepresentation).id || "",
            sourcePad: (sourcePad as PadEditorRepresentation).id || "",
            addPosition: position,
            close: () => setQuickAdd(undefined),
            portalInfo: {
              portalId: data.sourcePortalId as string,
              portalEnd: data.portalEnd as PortalEnd,
            },
          });
        }
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
            onClick={() => {
              if (isRunning) {
                showDragWarningThrottled(
                  "Can't add new nodes while app is running",
                );
                return;
              }
              setIsNodeLibraryOpen(!isNodeLibraryOpen);
            }}
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
      {
        <div className="absolute top-2 left-2 z-20">
          <RunId />
        </div>
      }

      <div
        className={`absolute top-0 left-0 right-0 bottom-0 transition-all duration-300 ease-in-out`}
      >
        <FlowErrorBoundary>
          <ReactFlow
            className=""
            nodes={reactFlowRepresentation.nodes}
            edges={reactFlowRepresentation.edges}
            onNodesChange={(changes) => {
              // Filter out dangerous changes while running
              const dangerousChanges = changes.filter(
                (change) =>
                  change.type === "position" || change.type === "remove",
              );

              if (isRunning && dangerousChanges.length > 0) {
                showDragWarningThrottled(
                  "Can't move or delete nodes while app is running",
                );
                // Only apply safe changes (like selection)
                const safeChanges = changes.filter(
                  (change) => change.type === "select",
                );
                if (safeChanges.length > 0) {
                  onReactFlowNodesChange(safeChanges);
                }
                return;
              }

              // Close node library if a node is selected
              const selectionChange = changes.find(
                (change) => change.type === "select",
              );
              if (selectionChange?.selected && isNodeLibraryOpen) {
                setIsNodeLibraryOpen(false);
              }
              onReactFlowNodesChange(changes);
            }}
            onEdgesChange={(changes) => {
              // Filter out dangerous changes while running
              const dangerousChanges = changes.filter(
                (change) => change.type === "remove",
              );

              if (isRunning && dangerousChanges.length > 0) {
                showDragWarningThrottled(
                  "Can't delete connections while app is running",
                );
                // Only apply safe changes (like selection)
                const safeChanges = changes.filter(
                  (change) => change.type === "select",
                );
                if (safeChanges.length > 0) {
                  onReactFlowEdgesChange(safeChanges);
                }
                return;
              }

              onReactFlowEdgesChange(changes);
            }}
            onConnect={(connection) => {
              if (isRunning) {
                showDragWarningThrottled(
                  "Can't create new connections while app is running",
                );
                return;
              }
              onReactFlowConnect(connection);
            }}
            onConnectEnd={onConnectEnd}
            edgeTypes={edgeTypes}
            connectionLineComponent={CustomConnectionLine}
            fitView
            nodeTypes={{
              node: BaseBlock,
              portal_start: PortalStart,
              portal_end: PortalEndComponent,
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
            nodesDraggable={true}
            nodesConnectable={true}
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
        {quickAdd && <QuickAddModal {...quickAdd} />}
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
  const { exportApp } = useRepository();

  const onClick = useCallback(async () => {
    try {
      const appExport = await exportApp(appId);
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
  }, [appId, exportApp, path]);

  if (!path.startsWith("/app/")) {
    return null;
  }

  return (
    <button
      onClick={onClick}
      title="Export"
      className="btn btn-sm gap-2 font-vt323 tracking-wider btn-primary group overflow-hidden transition-all duration-300 ease-in-out relative flex items-center justify-center w-10 hover:w-20"
    >
      <ArrowUpTrayIcon className="h-4 w-4 flex-shrink-0 absolute left-1/2 top-1/2 transform -translate-x-1/2 -translate-y-1/2 group-hover:opacity-0" />
      <span className="opacity-0 group-hover:opacity-100 transition-opacity duration-300 ease-in-out whitespace-nowrap">
        Share Graph
      </span>
    </button>
  );
}
