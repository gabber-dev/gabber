/**
 * Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
 * SPDX-License-Identifier: SUL-1.0
 */

import ReactModal from "react-modal";
import { useEditor } from "@/hooks/useEditor";
import { useNodeId } from "@xyflow/react";
export function StateMachineGraphMini() {
  const { clearAllSelection, setStateMachineEditing } = useEditor();
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
