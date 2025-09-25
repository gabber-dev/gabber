/**
 * Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
 * SPDX-License-Identifier: SUL-1.0
 */

import { NodeEditorRepresentation, UpdateNodeEdit } from "@/generated/editor";
import { useEditor } from "@/hooks/useEditor";
import { useRun } from "@/hooks/useRun";
import { Node, useNodeId, useNodesData } from "@xyflow/react";
import { useCallback, useRef, useState } from "react";
import toast from "react-hot-toast";

export function NodeId() {
  const nodeId = useNodeId();
  const nodeData = useNodesData<Node<NodeEditorRepresentation>>(nodeId || "");
  const [isEditing, setIsEditing] = useState(false);
  const [value, setValue] = useState(nodeId || "ERROR: NO ID");
  const inputRef = useRef<HTMLInputElement | null>(null);
  const { updateNode } = useEditor();
  const { connectionState } = useRun();
  const isRunning = connectionState === "connected" || connectionState === "connecting";

  const save = useCallback(
    (newId: string) => {
      const req: UpdateNodeEdit = {
        type: "update_node",
        id: nodeId || "",
        editor_name: nodeData?.data.editor_name || "",
        new_id: newId,
        editor_dimensions: nodeData?.data.editor_dimensions || [10, 10],
        editor_position: nodeData?.data.editor_position || [0, 0],
      };
      updateNode(req, isRunning);
    },
    [
      nodeData?.data.editor_dimensions,
      nodeData?.data.editor_name,
      nodeData?.data.editor_position,
      nodeId,
      updateNode,
      isRunning,
    ],
  );

  const handleDoubleClick = () => {
    setIsEditing(true);
    setTimeout(() => {
      inputRef.current?.focus();
      inputRef.current?.select();
    }, 0);
  };

  const handleBlur = () => {
    setIsEditing(false);
    if (value !== (nodeId || "ERROR: NO ID")) {
      save(value);
    }
  };

  const handleCopy = () => {
    navigator.clipboard.writeText(value);
    toast.success("Copied to clipboard");
  };

  return (
    <div className="flex items-center space-x-2 text-xs text-base-content/60 font-mono select-none">
      {isEditing ? (
        <input
          ref={inputRef}
          type="text"
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onBlur={handleBlur}
          onKeyDown={(e) => {
            if (e.key === "Enter") {
              handleBlur();
            } else if (e.key === "Escape") {
              setValue(nodeId || "ERROR: NO ID");
              setIsEditing(false);
            }
          }}
          className="flex-grow bg-transparent outline-none text-xs text-base-content/60 font-mono border border-base-content/30 p-1 nodrag select-text"
        />
      ) : (
        <>
          <span
            onDoubleClick={handleDoubleClick}
            className="cursor-pointer flex-grow"
          >
            {value}
          </span>
          <button
            onClick={handleCopy}
            className="text-base-content/60 nodrag cursor-pointer"
          >
            📋
          </button>
        </>
      )}
    </div>
  );
}
