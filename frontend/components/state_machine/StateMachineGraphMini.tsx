import { useState } from "react";
import ReactModal from "react-modal";
import { StateMachineGraphEdit } from "./StateMachineGraphEdit";
import { useEditor } from "@/hooks/useEditor";
import { useNodeId } from "@xyflow/react";
export function StateMachineGraphMini() {
  const { clearAllSelection, stateMachineEditing, setStateMachineEditing } =
    useEditor();
  const nodeId = useNodeId();
  return (
    <div className="flex flex-col items-center justify-center h-full pointer-events-none">
      <div
        ref={(el) => {
          if (el) {
            ReactModal.setAppElement(el);
          }
        }}
      />
      <button
        className="btn btn-primary btn-sm mb-2 pointer-events-auto"
        onClick={() => {
          setStateMachineEditing(nodeId || undefined);
          setTimeout(() => {
            clearAllSelection();
          }, 100);
        }}
      >
        Edit
      </button>
    </div>
  );
}
