/**
 * Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
 * SPDX-License-Identifier: SUL-1.0
 */

import { Handle, Position } from "@xyflow/react";
import { PadEditorRepresentation } from "@/generated/editor";
import { useMemo, useState } from "react";
import { getDataTypeColor, getPrimaryDataType } from "./utils/dataTypeColors";

type Props = {
  data: PadEditorRepresentation;
  forceVisible?: boolean;
  displayName?: string;
};

export function PadHandle({ data, forceVisible = false, displayName }: Props) {
  const [isModalOpen, setIsModalOpen] = useState(false);

  const direction = useMemo(() => {
    if (data.type.indexOf("Source") !== -1) {
      return "source";
    } else if (data.type.indexOf("Sink") !== -1) {
      return "target";
    }
    console.warn(
      `PadHandle: Unknown pad type ${data.type}. Defaulting to source.`,
    );
    return "source";
  }, [data]);

  const position = useMemo(() => {
    if (direction === "source") {
      return Position.Right;
    }
    return Position.Left;
  }, [direction]);

  // Create a unique position ID to avoid conflicts
  const uniquePositionId = useMemo(() => {
    return `${data.id}_${direction}`;
  }, [data.id, direction]);

  const hasConnections = useMemo(() => {
    if (direction === "source") {
      // For source pads, check if they have any next_pads
      return data.next_pads && data.next_pads.length > 0;
    } else {
      // For target pads, check if they have a previous_pad
      return data.previous_pad !== null;
    }
  }, [data.next_pads, data.previous_pad, direction]);

  const allowedTypeNames = useMemo<string[]>(() => {
    if (data.allowed_types) {
      if (data.allowed_types.length > 1) {
        return data.allowed_types.map((typeDef) => {
          return typeDef.type as string;
        });
      } else {
        const allowedType = data.allowed_types[0];
        if (allowedType.type === "enum") {
          const options = (allowedType.options || []) as string[];
          const optionsString = options.join(", ");
          return [`enum(${optionsString})`];
        }
        return [allowedType.type as string];
      }
    }
    return [];
  }, [data.allowed_types]);

  // Get the primary data type for color coding
  const primaryDataType = useMemo(() => {
    return getPrimaryDataType(data.allowed_types || []);
  }, [data.allowed_types]);

  // Get the color for the data type
  const dataTypeColor = useMemo(() => {
    return getDataTypeColor(primaryDataType || "default");
  }, [primaryDataType]);

  // Create dynamic styles for the handle
  const handleStyle = useMemo(() => {
    const baseStyle = {
      width: "18px",
      height: "18px",
      borderRadius: "9999px",
      border: `2px solid ${dataTypeColor.border}`,
      background: dataTypeColor.background,
      opacity: 0.9,
      boxSizing: "border-box" as const,
    };
    return baseStyle;
  }, [dataTypeColor]);

  return (
    <div
      className="relative items-center justify-center"
      onMouseEnter={() => setIsModalOpen(true)}
      onMouseLeave={() => setIsModalOpen(false)}
    >
      <Handle
        className="!w-3 !h-3"
        style={handleStyle}
        type={direction}
        position={position}
        id={uniquePositionId}
        isConnectable={true}
      />
      {hasConnections && (
        <div
          className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 pointer-events-none"
          style={{
            width: "18px",
            height: "18px",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
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
      {isModalOpen && (
        <div
          className={`absolute z-20 ${direction === "source" ? "-left-56" : "left-4"} -top-2 w-52 bg-base-200 border-2 border-primary rounded-lg shadow-lg p-3 text-sm`}
        >
          <div className="space-y-2">
            <div className="border-b border-primary/30 pb-2">
              <h3 className="text-accent font-medium">Pad Info</h3>
            </div>
            <div className="space-y-1">
              <div className="flex justify-between items-start">
                <span className="text-primary font-medium text-xs">ID:</span>
                <span className="text-accent text-xs break-all ml-2">
                  {displayName || data.id}
                </span>
              </div>
              <div className="flex justify-between items-start">
                <span className="text-primary font-medium text-xs">Type:</span>
                <span className="text-accent text-xs break-all ml-2">
                  {data.type}
                </span>
              </div>
              <div className="flex justify-between items-start">
                <span className="text-primary font-medium text-xs">
                  Direction:
                </span>
                <span className="text-accent text-xs break-all ml-2">
                  {direction}
                </span>
              </div>
              <div className="flex justify-between items-start">
                <span className="text-primary font-medium text-xs">
                  Allowed:
                </span>
                <div className="flex flex-wrap gap-1 ml-2">
                  {allowedTypeNames.length > 0 ? (
                    allowedTypeNames.map((name, idx) => (
                      <span
                        key={idx}
                        className="border rounded-sm text-xs px-1 text-accent break-normal"
                      >
                        {name}
                      </span>
                    ))
                  ) : (
                    <span className="text-accent text-xs">—</span>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
