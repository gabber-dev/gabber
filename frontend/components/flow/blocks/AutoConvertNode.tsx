/**
 * Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
 * SPDX-License-Identifier: SUL-1.0
 */

import { useState, useMemo } from "react";
import { Handle, Position, useNodeId } from "@xyflow/react";
import { ArrowRightIcon } from "@heroicons/react/24/outline";
import { useEditor } from "@/hooks/useEditor";
import {
  getDataTypeColor,
  getPrimaryDataType,
} from "./components/pads/utils/dataTypeColors";

export function AutoConvertNode() {
  const [hovered, setHovered] = useState(false);
  const nodeId = useNodeId();
  const { editorRepresentation } = useEditor();

  // Find the AutoConvert node data
  const nodeData = useMemo(() => {
    return editorRepresentation.nodes.find((node: any) => node.id === nodeId);
  }, [editorRepresentation.nodes, nodeId]);

  // Get input and output pad data
  const inputPad = useMemo(() => {
    if (!nodeData?.pads) return null;
    return nodeData.pads.find((pad: any) => pad.type.includes("Sink"));
  }, [nodeData?.pads]);

  const outputPad = useMemo(() => {
    if (!nodeData?.pads) return null;
    return nodeData.pads.find((pad: any) => pad.type.includes("Source"));
  }, [nodeData?.pads]);

  // Get data types for color coding
  const inputDataType = useMemo(() => {
    if (!inputPad) return null;
    return getPrimaryDataType(inputPad.allowed_types || []);
  }, [inputPad]);

  const outputDataType = useMemo(() => {
    if (!outputPad) return null;
    return getPrimaryDataType(outputPad.allowed_types || []);
  }, [outputPad]);

  // Determine if there are connections to show actual types
  const hasInputConnection = inputPad?.previous_pad !== null;
  const hasOutputConnection =
    outputPad?.next_pads && outputPad.next_pads.length > 0;

  // Use actual connected types if available, otherwise use allowed types
  const actualInputType = hasInputConnection ? inputDataType : null;
  const actualOutputType = hasOutputConnection ? outputDataType : null;

  // Final colors to use
  const finalInputColor = getDataTypeColor(
    actualInputType || inputDataType || "default",
  );
  const finalOutputColor = getDataTypeColor(
    actualOutputType || outputDataType || "default",
  );

  return (
    <div
      className={`
        relative flex items-center justify-center
        w-20 h-12 rounded-lg border-2 border-warning bg-neutral
        shadow-md
        ${hovered ? "ring-4 ring-warning/40" : ""}
      `}
      title="Auto Convert"
    >
      {/* Input handle (sink) */}
      <Handle
        type="target"
        position={Position.Left}
        className="!w-5 !h-5 !bg-transparent !border-none z-10 flex items-center justify-center cursor-pointer"
        id="sink"
        onMouseEnter={() => setHovered(true)}
        onMouseLeave={() => setHovered(false)}
      >
        <div
          className="w-3.5 h-3.5 rounded-full border-2 border-white pointer-events-none relative"
          style={{
            background: finalInputColor.background,
            borderColor: finalInputColor.border,
          }}
        />
      </Handle>
      {hasInputConnection && (
        <div
          className="absolute left-0 top-1/2 transform -translate-x-1/2 -translate-y-1/2 flex items-center justify-center pointer-events-none z-20"
          style={{
            width: "14px",
            height: "14px",
          }}
        >
          <div
            className="w-1 h-1 rounded-full bg-base-100"
            style={{
              opacity: 0.8,
            }}
          />
        </div>
      )}
      {/* Output handle (source) */}
      <Handle
        type="source"
        position={Position.Right}
        className="!w-5 !h-5 !bg-transparent !border-none z-10 flex items-center justify-center cursor-pointer"
        id="source"
        onMouseEnter={() => setHovered(true)}
        onMouseLeave={() => setHovered(false)}
      >
        <div
          className="w-3.5 h-3.5 rounded-full border-2 border-white pointer-events-none relative"
          style={{
            background: finalOutputColor.background,
            borderColor: finalOutputColor.border,
          }}
        />
      </Handle>
      {hasOutputConnection && (
        <div
          className="absolute right-0 top-1/2 transform translate-x-1/2 -translate-y-1/2 flex items-center justify-center pointer-events-none z-20"
          style={{
            width: "14px",
            height: "14px",
          }}
        >
          <div
            className="w-1 h-1 rounded-full bg-black"
            style={{
              opacity: 0.8,
            }}
          />
        </div>
      )}

      {/* Three icons: Circle, Arrow, Square */}
      <div className="flex items-center justify-center gap-2 px-2">
        {/* Circle icon */}
        <div className="w-4 h-4 rounded-full border-2 border-warning bg-transparent" />

        {/* Arrow icon */}
        <ArrowRightIcon className="text-warning w-4 h-4" />

        {/* Square icon */}
        <div className="w-4 h-4 border-2 border-warning bg-transparent" />
      </div>
    </div>
  );
}
