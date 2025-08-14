/**
 * Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
 * SPDX-License-Identifier: SUL-1.0
 */

import { PadEditorRepresentation } from "@/generated/editor";
import { PadHandle } from "./PadHandle";
import { useStatelessPad } from "./hooks/useStatelessPad";
import { useRun } from "@/hooks/useRun";
import { useNodeId } from "@xyflow/react";
import { useSourcePad, usePad } from "@gabber/client-react";
import { useEffect, useState } from "react";

type Props = {
  data: PadEditorRepresentation;
};

export function StatelessPad({ data }: Props) {
  const isSource = data.type.indexOf("Source") !== -1;
  const { singleAllowedType } = useStatelessPad(data.id);
  const { connectionState } = useRun();
  const nodeId = useNodeId();
  const { pushValue } = useSourcePad(nodeId || "error", data.id);
  const [isActive, setIsActive] = useState(false);
  const { lastValue } = usePad(nodeId || "error", data.id);

  const isTrigger = singleAllowedType?.type === "trigger";
  const isStatelessPad = data.type === "StatelessSourcePad" || data.type === "StatelessSinkPad";
  const hasConnections = isSource ? 
    (data.next_pads && data.next_pads.length > 0) : 
    data.previous_pad !== null;

  useEffect(() => {
    // Only animate if:
    // 1. For stateless pads (both source and sink): when they have values AND connections
    // 2. For property pads: don't animate
    if (lastValue && isStatelessPad && hasConnections) {
      setIsActive(true);
      const timer = setTimeout(() => {
        setIsActive(false);
      }, 300); // 300ms animation duration
      return () => clearTimeout(timer);
    }
  }, [lastValue, isStatelessPad, hasConnections]);

  return (
    <div
      className={`relative w-full flex items-center ${isSource ? "justify-end" : "justify-start"}`}
    >
      <div
        className={`flex gap-2 items-center ${isSource ? "flex-row" : "flex-row-reverse"}`}
      >
        {isTrigger && isSource && connectionState === "connected" && (
          <button
            className="btn btn-secondary btn-sm px-1 text-xs py-0 h-5 box-border"
            onClick={async () => {
              pushValue({ value: "trigger" });
            }}
          >
            Test
          </button>
        )}
        <div className={`text-sm text-accent font-medium transition-all duration-300 ${isActive ? 'opacity-100 scale-110' : 'opacity-75 scale-100'}`}>
          {data.id}
        </div>

        <div className={`absolute ${isSource ? "-right-4" : "-left-4"}`}>
          <PadHandle data={data} isActive={isActive} />
        </div>
      </div>
    </div>
  );
}
