/**
 * Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
 * SPDX-License-Identifier: SUL-1.0
 */

import { PadEditorRepresentation } from "@/generated/editor";
import { PadHandle } from "./PadHandle";
import { useStatelessPad } from "./hooks/useStatelessPad";
import { useRun } from "@/hooks/useRun";
import { useNodeId } from "@xyflow/react";
import { useSourcePad } from "@gabber/client-react";

type Props = {
  data: PadEditorRepresentation;
  forceVisible?: boolean;
  displayName?: string;
};

export function StatelessPad({ data, forceVisible = false, displayName }: Props) {
  const isSource = data.type.indexOf("Source") !== -1;
  const { singleAllowedType } = useStatelessPad(data.id);
  const { connectionState } = useRun();
  const nodeId = useNodeId();
  const { pushValue } = useSourcePad(nodeId || "error", data.id);

  const isTrigger = singleAllowedType?.type === "trigger";

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
        <div className={`absolute ${isSource ? "-right-4" : "-left-4"}`}>
          <PadHandle data={data} forceVisible={forceVisible} displayName={displayName} />
        </div>
      </div>
    </div>
  );
}
