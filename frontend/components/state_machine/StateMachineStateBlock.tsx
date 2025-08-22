/**
 * Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
 * SPDX-License-Identifier: SUL-1.0
 */

import { Handle, Node, Position, useNodeId, useNodesData } from "@xyflow/react";
import { ChangeEvent, useCallback, useMemo, useState } from "react";
import { PencilSquareIcon } from "@heroicons/react/24/outline";
import { StateMachineState } from "@/generated/stateMachine";
import { useStateMachine } from "./useStateMachine";

export function StateMachineStateBlock() {
  const nodeId = useNodeId();
  const nodeData = useNodesData<Node<StateMachineState>>(nodeId || "");
  const isEntry = nodeId === "__ENTRY__";
  const isAny = nodeId === "__ANY__";
  const [isEditing, setIsEditing] = useState(false);
  const { selectedNodes, updateState } = useStateMachine();

  const handleNameChange = useCallback(
    (e: ChangeEvent<HTMLInputElement>) => {
      if (!isEntry) {
        updateState(nodeId || "", e.target.value);
      }
    },
    [isEntry, nodeId, updateState],
  );

  const handleDoubleClick = useCallback(() => {
    if (!isEntry && !isAny) {
      setIsEditing(true);
    }
  }, [isAny, isEntry]);

  const handleBlur = useCallback(() => {
    setIsEditing(false);
  }, []);

  const name = useMemo(() => {
    if (isAny) {
      return "Any State";
    }
    return isEntry ? "Entry" : nodeData?.data?.name || "";
  }, [isAny, isEntry, nodeData?.data?.name]);

  const bgColor = useMemo(() => {
    if (isAny) {
      return "bg-info";
    }
    if (isEntry) {
      return "bg-success";
    }
    return "bg-primary";
  }, [isAny, isEntry]);

  const isSelected = useMemo(() => {
    return selectedNodes.includes(nodeId || "");
  }, [selectedNodes, nodeId]);

  return (
    <div className="relative min-w-14 h-8 group">
      <div
        className={`h-full relative z-10 flex flex-col items-center justify-center ${bgColor} rounded-full text-sm text-base-100 font-bold px-3 py-1`}
        onDoubleClick={handleDoubleClick}
      >
        {isEditing ? (
          <input
            type="text"
            value={name || ""}
            onChange={handleNameChange}
            onBlur={handleBlur}
            onFocus={(e) => e.target.select()}
            autoFocus
            className="w-full text-center bg-transparent border-none outline-none text-base-100 nodrag"
          />
        ) : (
          <div className="flex items-center gap-1">
            <p className="px-1">{name}</p>
            {!isEntry && (
              <button
                type="button"
                className="nodrag p-0 m-0 bg-transparent border-none cursor-pointer"
                onClick={(e) => {
                  e.stopPropagation();
                  setIsEditing(true);
                }}
                title="Rename state"
              >
                <PencilSquareIcon className="w-3.5 h-3.5 opacity-0 group-hover:opacity-70 transition-opacity" />
              </button>
            )}
          </div>
        )}
      </div>
      <Handle
        className="!absolute !inset-0 !-left-2 !-right-2 !-top-2 !-bottom-2 !border-4 !border-white !bg-transparent !rounded-full !z-5 !transform-none"
        type="source"
        position={Position.Right}
      />
      <Handle
        className="!absolute !inset-0 !-left-2 !-right-2 !-top-2 !-bottom-2 !border-white !bg-transparent !rounded-full !z-5 !transform-none"
        type="target"
        position={Position.Left}
      />
      {isSelected && (
        <div className="absolute inset-0 border-2 border-blue-500 rounded-full pointer-events-none z-20" />
      )}
    </div>
  );
}
