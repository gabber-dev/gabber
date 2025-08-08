import {
  Handle,
  Node,
  Position,
  useNodeId,
  useNodes,
  useNodesData,
  useNodesState,
} from "@xyflow/react";
import { ChangeEvent, useCallback, useMemo, useState } from "react";
import { StateMachineState } from "@/generated/stateMachine";
import { useStateMachine } from "./useStateMachine";

export function StateMachineStateBlock() {
  const nodeId = useNodeId();
  const nodeData = useNodesData<Node<StateMachineState>>(nodeId || "");
  const isEntry = nodeId === "__ENTRY__";
  const [isEditing, setIsEditing] = useState(false);
  const { selectedNodes, selectedEdges } = useStateMachine();

  const selected = useMemo(() => {
    return selectedNodes.includes(nodeId || "");
  }, [selectedNodes, nodeId]);

  const handleNameChange = useCallback(
    (e: ChangeEvent<HTMLInputElement>) => {
      if (!isEntry) {
      }
    },
    [isEntry],
  );

  const handleDoubleClick = useCallback(() => {
    if (!isEntry) {
      setIsEditing(true);
    }
  }, [isEntry]);

  const handleBlur = useCallback(() => {
    setIsEditing(false);
  }, []);

  const name = useMemo(() => {
    return isEntry ? "Entry" : nodeData?.data?.name || "ERROR";
  }, [isEntry, nodeData?.data?.name]);

  const bgColor = isEntry ? "bg-success" : "bg-primary";
  const borderClass = selected ? "border-4 border-white" : "border-transparent";

  return (
    <div className={`flex flex-col rounded-lg ${borderClass}`}>
      <div className="h-2 bg-gray-500 rounded-t-lg drag-handle cursor-move" />
      <div
        className={`relative z-10 flex flex-col items-center justify-center ${bgColor} p-2 rounded-b-lg text-sm text-base-100 font-bold`}
        onDoubleClick={handleDoubleClick}
      >
        {isEditing ? (
          <input
            type="text"
            value={name || ""}
            onChange={handleNameChange}
            onBlur={handleBlur}
            autoFocus
            className="w-full text-center bg-transparent border-none outline-none text-base-100 nodrag"
          />
        ) : (
          <p>{name}</p>
        )}
        <Handle
          className="!absolute !inset-0 !-left-2 !-right-2 !-top-2 !-bottom-2 !border-transparent !bg-transparent !rounded-lg !z-[-1] !transform-none"
          type="source"
          position={Position.Right}
        />
        <Handle
          className="!absolute !inset-0 !-left-2 !-right-2 !-top-2 !-bottom-2 !border-transparent !bg-transparent !rounded-lg !z-[-1] !transform-none"
          type="target"
          position={Position.Left}
        />
      </div>
    </div>
  );
}
