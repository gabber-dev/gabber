/**
 * Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
 * SPDX-License-Identifier: SUL-1.0
 */

import { MinusIcon, PlusIcon } from "@heroicons/react/24/outline";
import { useEditor } from "@/hooks/useEditor";
import { BaseBlockProps } from "./BaseBlock";
import { usePropertyPad } from "./components/pads/hooks/usePropertyPad";
import { useNodeId } from "@xyflow/react";
import { PadHandle } from "./components/pads/PadHandle";
import { PropertyPad } from "./components/pads/PropertyPad";
import { PropertyEdit } from "./components/pads/property_edit/PropertyEdit";

export function CompareNode({ data }: BaseBlockProps) {
  const {} = useEditor();
  return (
    <div className="w-48 flex flex-col bg-base-200 border-2 border-black border-b-4 border-r-4 rounded-lg relative">
      <div className="flex w-full items-center gap-2 bg-base-300 border-b-2 border-black p-3 rounded-t-lg drag-handle cursor-grab active:cursor-grabbing">
        <div className="flex-1">
          <h2 className="text-lg text-purple-400 font-medium">
            {data.editor_name}
          </h2>
          <div className="text-xs text-purple-400/60 font-mono">{data.id}</div>
        </div>
      </div>
      <div>
        <Mode />
        <Parameters />
      </div>
    </div>
  );
}

function Mode() {
  const nodeId = useNodeId();
  return (
    <div className="flex flex-col items-center border-b border-base-100 p-2">
      <PropertyEdit padId={"mode"} nodeId={nodeId || ""} />
      <div className="italic text-xs text-base-content/60">mode</div>
    </div>
  );
}

function Parameters() {
  const nodeId = useNodeId();
  const { editorValue, setEditorValue } = usePropertyPad<number>(
    nodeId || "",
    "num_conditions",
  );
  const modePad = usePropertyPad<string>(nodeId || "", "mode");
  return (
    <div className="flex flex-col">
      <div className="flex items-center justify-between p-2 bg-base-300 border-b border-black">
        <h3>Parameters</h3>
        <div className="flex gap-1">
          <button
            className="btn btn-sm btn-success p-0 m-0 w-4 h-4"
            onClick={() => {
              setEditorValue((editorValue || 0) + 1);
            }}
          >
            <PlusIcon className="w-full h-full" />
          </button>
          <button
            className="btn btn-sm btn-error p-0 m-0 w-4 h-4"
            onClick={() => {
              if (editorValue && editorValue > 0) {
                setEditorValue(editorValue - 1);
              }
            }}
          >
            <MinusIcon className="w-full h-full" />
          </button>
        </div>
      </div>
      <div>
        <div className="p-2">
          {(() => {
            for (let i = 0; i < (editorValue || 0); i++) {
              return (
                <>
                  <Parameter idx={i} />
                  {i !== (editorValue || 0) - 1 && (
                    <div className="divider text-xs italic text-base-content/60 m-2">
                      {modePad.editorValue || "ERROR"}
                    </div>
                  )}
                </>
              );
            }
          })()}
        </div>
      </div>
    </div>
  );
}

function Parameter({ idx }: { idx: number }) {
  const nodeId = useNodeId();
  const padA = usePropertyPad(nodeId || "", `condition_${idx}_A`);
  const padB = usePropertyPad(nodeId || "", `condition_${idx}_B`);
  const padOperator = usePropertyPad<string>(
    nodeId || "",
    `condition_${idx}_operator`,
  );

  if (!padA.pad || !padB.pad || !padOperator.pad) {
    console.warn(`Pads for condition ${idx} are not available.`);
    return <div></div>;
  }

  return (
    <div className="flex items-center w-full border-base-100">
      <div className="flex w-full flex-col gap-1">
        <div className="relative flex basis-0 grow items-center">
          {padA.pad && (
            <div className="absolute -left-2">
              <PadHandle data={padA.pad} />
            </div>
          )}{" "}
          <PropertyEdit padId={padA.pad.id} nodeId={nodeId || ""} />
        </div>
        <PropertyEdit padId={padOperator.pad.id} nodeId={nodeId || ""} />
        <div className="relative flex basis-0 grow items-center">
          {padB.pad && (
            <div className="absolute -left-2">
              <PadHandle data={padB.pad} />
            </div>
          )}{" "}
          <PropertyEdit padId={padB.pad.id} nodeId={nodeId || ""} />
        </div>
      </div>
    </div>
  );
}
