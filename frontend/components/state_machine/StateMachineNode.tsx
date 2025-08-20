/**
 * Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
 * SPDX-License-Identifier: SUL-1.0
 */

import { MinusIcon, PlusIcon } from "@heroicons/react/24/outline";
import { BaseBlockProps } from "../flow/blocks/BaseBlock";
import { useEditor } from "@/hooks/useEditor";
import {
  StateMachineParameterPads,
  StateMachineProvider,
  useStateMachine,
} from "./useStateMachine";
import { StateMachineGraphMini } from "./StateMachineGraphMini";
import { usePropertyPad } from "../flow/blocks/components/pads/hooks/usePropertyPad";
import { useNodeId } from "@xyflow/react";
import { PadHandle } from "../flow/blocks/components/pads/PadHandle";

export function StateMachineNode({ data }: BaseBlockProps) {
  const {} = useEditor();
  return (
    <div className="min-w-64 flex flex-col bg-base-200 border-2 border-black border-b-4 border-r-4 rounded-lg relative">
      <div className="flex w-full items-center gap-2 bg-base-300 border-b-2 border-black p-3 rounded-t-lg drag-handle cursor-grab active:cursor-grabbing">
        <div className="flex-1">
          <h2 className="text-lg text-purple-400 font-medium">
            {data.editor_name}
          </h2>
          <div className="text-xs text-purple-400/60 font-mono">{data.id}</div>
        </div>
      </div>
      <div>
        <StateMachineProvider nodeId={data.id}>
          <CurrentState />
          <Parameters />
          <StateMachineGraphMini />
        </StateMachineProvider>
      </div>
    </div>
  );
}

function Parameters() {
  const { addParameter, removeParameter, parameterPads } = useStateMachine();

  return (
    <div className="flex flex-col">
      <div className="flex items-center justify-between p-2 bg-base-300 border-b border-black">
        <h3>Parameters</h3>
        <div className="flex gap-2">
          <button
            className="btn btn-sm btn-success p-0 m-0 w-4 h-4"
            onClick={addParameter}
          >
            <PlusIcon className="w-full h-full" />
          </button>
          <button
            className="btn btn-sm btn-error p-0 m-0 w-4 h-4"
            onClick={removeParameter}
          >
            <MinusIcon className="w-full h-full" />
          </button>
        </div>
      </div>
      <div>
        {parameterPads.map((pads) => (
          <Parameter key={pads.namePadId} pads={pads} />
        ))}
      </div>
    </div>
  );
}

function CurrentState() {
  const { runtimeValue, editorValue, pad } = usePropertyPad<string>(
    useNodeId() || "",
    "current_state",
  );

  return (
    <div className="flex items-center justify-between p-2 border-b border-black">
      <div className="relative flex flex-col items-center gap-1 grow-5 basis-0 pb-4">
        {runtimeValue !== "" ? (
          <div className="text-sm border border-base-300 bg-base-100 px-2 py-1 rounded">
            {runtimeValue ?? ""}
          </div>
        ) : (
          <div className="text-sm text-base-content/60">⚠️ no states</div>
        )}
        <label className="italic absolute bottom-0 label text-xs text-base-content/50">
          Current State
          {runtimeValue !== editorValue &&
            runtimeValue !== undefined &&
            editorValue !== undefined && <span className="ml-1">*</span>}
        </label>
      </div>
      {pad && (
        <div className="absolute right-0">
          <PadHandle data={pad} />
        </div>
      )}
    </div>
  );
}

function Parameter({ pads }: { pads: StateMachineParameterPads }) {
  const nodeId = useNodeId();
  const { runtimeValue: name, setEditorValue } = usePropertyPad<string>(
    nodeId || "",
    pads.namePadId,
  );
  const { pad } = usePropertyPad<unknown>(nodeId || "", pads.valuePadId);

  console.log("NEIL Parameter pads", pad, nodeId, pads);

  return (
    <div className="flex items-center border-b border-base-100 p-2">
      <div className="flex gap-2">
        <div className="relative flex basis-0 grow items-center">
          {pad && (
            <div className="absolute -left-2">
              <PadHandle data={pad} />
            </div>
          )}{" "}
          <div className="text-sm ml-1">value</div>
        </div>
        <div className="relative flex flex-col gap-1 grow-5 basis-0 pb-4">
          <input
            className="input input-sm !outline-none"
            value={name || ""}
            onChange={(e) => setEditorValue(e.target.value)}
          />
          <label className="italic absolute bottom-0 label text-xs">
            Parameter Name
          </label>
        </div>
      </div>
    </div>
  );
}
