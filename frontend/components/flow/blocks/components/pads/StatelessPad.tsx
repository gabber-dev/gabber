/**
 * Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
 * SPDX-License-Identifier: SUL-1.0
 */

import { useCallback } from "react";
import { PadEditorRepresentation } from "@/generated/editor";
import { PadHandle } from "./PadHandle";
import { useStatelessPad } from "./hooks/useStatelessPad";
import { useRealtimeSessionEngine } from "gabber-client-react";
import { useRun } from "@/hooks/useRun";
import { useNodeId } from "@xyflow/react";

type Props = {
  data: PadEditorRepresentation;
};

export function StatelessPad({ data }: Props) {
  const isSource = data.type.indexOf("Source") !== -1;
  const nodeId = useNodeId();
  const { singleAllowedType } = useStatelessPad(data.id);
  const { connectionState } = useRun();
  const { innerEngine } = useRealtimeSessionEngine();

  const debugTrigger = useCallback(async () => {
    const topic = `${nodeId}:${data.id}:trigger`;
    await (innerEngine as any).livekitRoom?.localParticipant.publishData(
      new Uint8Array([1]),
      {
        topic,
      },
    );
    const rawMessage = `Trigger debug message sent for topic: ${topic}`;
    console.log(rawMessage);
  }, [data.id, innerEngine, nodeId]);

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
            onClick={() => {
              debugTrigger();
            }}
          >
            Test
          </button>
        )}
        <div className="text-sm text-accent font-medium">{data.id}</div>

        <div className={`absolute ${isSource ? "-right-4" : "-left-4"}`}>
          <PadHandle data={data} />
        </div>
      </div>
    </div>
  );
}
