import { Handle, Position, useNodeId } from "@xyflow/react";
import { ChangeEvent, useCallback, useState } from "react";

export function StateMachineStateBlock() {
  const nodeId = useNodeId();
  const isEntry = nodeId === "__ENTRY__";
  const [name, setName] = useState(isEntry ? "Entry" : "State");
  const [isEditing, setIsEditing] = useState(false);

  const handleNameChange = useCallback(
    (e: ChangeEvent<HTMLInputElement>) => {
      if (!isEntry) {
        setName(e.target.value);
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

  const bgColor = isEntry ? "bg-success" : "bg-primary";

  return (
    <div className="relative">
      <div
        className={`relative z-10 flex flex-col items-center justify-center ${bgColor} p-2 rounded-full text-sm text-base-100 font-bold`}
        onDoubleClick={handleDoubleClick}
      >
        {isEditing ? (
          <input
            type="text"
            value={name}
            onChange={handleNameChange}
            onBlur={handleBlur}
            autoFocus
            className="w-full text-center bg-transparent border-none outline-none text-base-100"
          />
        ) : (
          <p>{name}</p>
        )}
      </div>
      <Handle
        className="!absolute !inset-0 !-left-2 !-right-2 !-top-2 !-bottom-2 !border-4 !border-white !bg-transparent !rounded-full !z-0 !transform-none"
        type="source"
        position={Position.Right}
      />
    </div>
  );
}
