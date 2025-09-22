/**
 * Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
 * SPDX-License-Identifier: SUL-1.0
 */

import { MinusIcon, PlusIcon } from "@heroicons/react/24/outline";
import { BaseBlockProps } from "./BaseBlock";
import { usePropertyPad } from "./components/pads/hooks/usePropertyPad";
import { useNodeId, useNodesData, Node } from "@xyflow/react";
import { PadHandle } from "./components/pads/PadHandle";
import { PropertyEdit } from "./components/pads/property_edit/PropertyEdit";
import { useMemo } from "react";
import { NodeEditorRepresentation } from "@/generated/repository";
import { NodeName } from "./components/NodeName";
import { NodeId } from "./components/NodeId";

export function CompareNode({}: BaseBlockProps) {
  return (
    <div className="w-54 flex flex-col bg-base-200 border-2 border-black border-b-4 border-r-4 rounded-lg relative">
      <div className="flex w-full items-center gap-2 bg-base-300 border-b-2 border-black p-3 rounded-t-lg drag-handle cursor-grab active:cursor-grabbing">
        <div className="flex-1">
          <NodeName />
          <NodeId />
        </div>
      </div>
      <div className="p-2">
        <div className="flex flex-col items-center gap-1 w-full">
          <Mode />
          <ValuePad />
          <AddRemoveCondition />
        </div>

        <div className="divider w-full m-0" />
        <AllConditions />
      </div>
    </div>
  );
}

function ValuePad() {
  const nodeId = useNodeId();
  const pad = usePropertyPad(nodeId || "", "value");
  if (!pad.pad) return null;
  return (
    <div className="relative w-full flex gap-2 justify-between pr-2 basis-0 grow items-center">
      <div className="text-xs italic text-base-content/60">Current Value:</div>
      {pad.pad && (
        <div className="absolute -right-2">
          <PadHandle data={pad.pad} />
        </div>
      )}{" "}
      {pad.singleAllowedType ? (
        <PropertyEdit padId={pad.pad.id} nodeId={nodeId || ""} />
      ) : (
        <div className="text-xs pl-2">Value</div>
      )}
    </div>
  );
}

function Mode() {
  const nodeId = useNodeId();

  return (
    <div className="flex w-full justify-between items-center gap-2">
      <div className="italic text-xs text-base-content/60">Mode:</div>
      <PropertyEdit padId={"mode"} nodeId={nodeId || ""} />
    </div>
  );
}

function AddRemoveCondition() {
  const nodeId = useNodeId();
  const { editorValue, setEditorValue } = usePropertyPad<number>(
    nodeId || "",
    "num_conditions",
  );
  return (
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
  );
}

function AllConditions() {
  const nodeId = useNodeId();
  const node = useNodesData<Node<NodeEditorRepresentation>>(nodeId || "");
  const { runtimeValue: modeValue } = usePropertyPad<string>(
    nodeId || "",
    "mode",
  );

  const indexes = useMemo(() => {
    if (!node || !node.data) return [];
    const res: number[] = [];
    for (const p of node.data.pads) {
      if (p.id.startsWith("condition_")) {
        const idx = Number(p.id.split("_")[1]);
        if (isNaN(idx)) continue; // Skip if idx is not a number
        if (res.includes(idx)) continue; // Skip if idx already exists
        res.push(idx);
      }
    }
    return res;
  }, [node]);

  return (
    <div className="flex flex-col">
      {indexes.map((idx) => (
        <div key={idx} className="flex items-center gap-2 flex-col">
          <Condition idx={idx} />
          {idx !== indexes.length - 1 && (
            <div className="divider text-xs p-0 m-0">
              {modeValue || "ERROR: mode not set"}
            </div>
          )}
        </div>
      ))}
    </div>
  );
}

function Condition({ idx }: { idx: number }) {
  const nodeId = useNodeId();
  const padA = usePropertyPad(nodeId || "", `condition_${idx}_A`);
  const padB = usePropertyPad(nodeId || "", `condition_${idx}_B`);
  const padOperator = usePropertyPad<string>(
    nodeId || "",
    `condition_${idx}_operator`,
  );

  if (!padA.pad || !padB.pad || !padOperator.pad) {
    return null;
  }

  return (
    <div className="flex items-center w-full border-base-100">
      <div className="flex w-full flex-col gap-1">
        <div className="relative flex basis-0 grow items-center">
          {padA.pad && (
            <div className="absolute -left-2">
              <PadHandle data={padA.pad} notes={[]} />
            </div>
          )}{" "}
          {padA.singleAllowedType ? (
            <PropertyEdit padId={padA.pad.id} nodeId={nodeId || ""} />
          ) : (
            <div className="text-xs pl-2">A</div>
          )}
        </div>
        <PropertyEdit padId={padOperator.pad.id} nodeId={nodeId || ""} />
        <div className="relative flex basis-0 grow items-center">
          {padB.pad && (
            <div className="absolute -left-2">
              <PadHandle data={padB.pad} notes={[]} />
            </div>
          )}{" "}
          {padB.singleAllowedType ? (
            <PropertyEdit padId={padB.pad.id} nodeId={nodeId || ""} />
          ) : (
            <div className="text-xs pl-2">B</div>
          )}
        </div>
      </div>
    </div>
  );
}
