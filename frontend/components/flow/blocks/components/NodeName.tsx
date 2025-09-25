/**
 * Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
 * SPDX-License-Identifier: SUL-1.0
 */

import { NodeEditorRepresentation, UpdateNodeEdit } from "@/generated/editor";
import { useEditor } from "@/hooks/useEditor";
import { useRun } from "@/hooks/useRun";
import { Node, useNodeId, useNodesData } from "@xyflow/react";
import { useCallback, useRef, useState } from "react";

export function NodeName() {
  const nodeId = useNodeId();
  const nodeData = useNodesData<Node<NodeEditorRepresentation>>(nodeId || "");
  const [isEditing, setIsEditing] = useState(false);
  const [value, setValue] = useState(
    nodeData?.data.editor_name || "ERROR: NO NAME",
  );
  const inputRef = useRef<HTMLInputElement | null>(null);
  const { updateNode } = useEditor();
  const { connectionState } = useRun();
  const isRunning = connectionState === "connected" || connectionState === "connecting";

  const save = useCallback(
    (newName: string) => {
      const req: UpdateNodeEdit = {
        type: "update_node",
        id: nodeId || "",
        editor_name: newName,
        new_id: nodeId || "",
        editor_dimensions: nodeData?.data.editor_dimensions || [10, 10],
        editor_position: nodeData?.data.editor_position || [0, 0],
      };
      updateNode(req, isRunning);
    },
    [
      nodeData?.data.editor_dimensions,
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
    if (value !== (nodeData?.data.editor_name || "ERROR: NO NAME")) {
      save(value);
    }
  };

  return (
    <div className="text-lg text-primary font-medium select-none">
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
              setValue(nodeData?.data.editor_name || "ERROR: NO NAME");
              setIsEditing(false);
            }
          }}
          className="bg-transparent outline-none text-lg text-primary font-medium border border-primary/30 p-1 nodrag select-text"
        />
      ) : (
        <span onDoubleClick={handleDoubleClick} className="cursor-pointer">
          {value}
        </span>
      )}
    </div>
  );
}
