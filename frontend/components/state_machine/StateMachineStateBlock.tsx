import { Handle, Node, Position, useNodeId, useNodesData } from "@xyflow/react";
import { ChangeEvent, useCallback, useMemo, useState } from "react";
import { StateMachineState } from "@/generated/stateMachine";
import { useStateMachine } from "./useStateMachine";

export function StateMachineStateBlock() {
  const nodeId = useNodeId();
  const nodeData = useNodesData<Node<StateMachineState>>(nodeId || "");
  const isEntry = nodeId === "__ENTRY__";
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

  const isSelected = useMemo(() => {
    return selectedNodes.includes(nodeId || "");
  }, [selectedNodes, nodeId]);

  return (
    <div className="relative">
      <div
        className={`relative z-10 flex flex-col items-center justify-center ${bgColor} p-2 rounded-full text-sm text-base-100 font-bold`}
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
