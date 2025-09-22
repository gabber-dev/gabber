/**
 * Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
 * SPDX-License-Identifier: SUL-1.0
 */

import { Handle, Position } from "@xyflow/react";
import { NodeNote, PadEditorRepresentation } from "@/generated/editor";
import { useMemo, useState, useRef } from "react";
import { getDataTypeColor, getPrimaryDataType } from "./utils/dataTypeColors";
import { ExclamationTriangleIcon } from "@heroicons/react/24/solid";
import { PadInfo } from "./PadInfo";

type Props = {
  data: PadEditorRepresentation;
  notes: NodeNote[];
  isActive?: boolean;
};

export function PadHandle({ data, isActive = false, notes }: Props) {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const timeoutRef = useRef<NodeJS.Timeout | null>(null);

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

  const hasConnections = useMemo(() => {
    if (direction === "source") {
      // For source pads, check if they have any next_pads
      return data.next_pads && data.next_pads.length > 0;
    } else {
      // For target pads, check if they have a previous_pad
      return data.previous_pad !== null;
    }
  }, [data.next_pads, data.previous_pad, direction]);

  const allowedTypeNames = useMemo<string[] | null>(() => {
    if (data.allowed_types === null || data.allowed_types === undefined)
      return null;
    if (data.allowed_types.length === 1) {
      const allowedType = data.allowed_types[0];
      if (allowedType.type === "enum") {
        const options = (allowedType.options || []) as string[];
        const optionsString = options.join(", ");
        return [`enum(${optionsString})`];
      }
      return [allowedType.type as string];
    }

    return data.allowed_types.map((t) => t.type as string);
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
    const baseTranslate =
      direction === "source" ? "translate(50%, -50%)" : "translate(-50%, -50%)";
    const baseStyle = {
      width: "12px",
      height: "12px",
      borderRadius: "9999px",
      border: hasConnections ? `2px solid ${dataTypeColor.border}` : "none",
      background: dataTypeColor.background,
      backgroundImage: hasConnections
        ? `radial-gradient(circle at center, #000 30%, ${dataTypeColor.background} 32%)`
        : "none",
      opacity: hasConnections ? 0.9 : 0.7,
      boxSizing: "border-box" as const,
      transition:
        "transform 300ms ease-in-out, box-shadow 300ms ease-in-out, opacity 150ms ease-in-out",
      transform: `${baseTranslate} ${isActive ? "scale(1.2)" : "scale(1)"}`,
      boxShadow: isActive ? `0 0 8px ${dataTypeColor.border}` : "none",
    } as const;
    return baseStyle;
  }, [hasConnections, dataTypeColor, isActive, direction]);

  const handleMouseEnter = () => {
    setIsModalOpen(true);
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
      timeoutRef.current = null;
    }
  };

  const handleMouseLeave = () => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }
    timeoutRef.current = setTimeout(() => {
      setIsModalOpen(false);
      timeoutRef.current = null;
    }, 300);
  };

  return (
    <div
      className="relative items-center justify-center"
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
    >
      {notes.length > 0 && (
        <div
          className={`absolute ${position === Position.Right ? "-top-2 left-2" : "-top-2 right-2"} w-4 h-4`}
        >
          <ExclamationTriangleIcon />
        </div>
      )}
      <div
        className="absolute"
        style={{
          top: "50%",
          [position === Position.Right ? "right" : "left"]: 0,
        }}
      >
        <Handle
          style={handleStyle}
          type={direction}
          position={position}
          id={data.id}
        />
      </div>
      {/* inner dot rendered via backgroundImage when connected */}
      {isModalOpen && (
        <div
          className={`absolute z-20 ${direction === "source" ? "-left-68" : "left-4"} -top-2 w-64 bg-base-200 border-2 border-primary rounded-lg shadow-lg p-3 text-sm`}
        >
          <PadInfo
            data={data}
            direction={direction === "source" ? "source" : "sink"}
            allowedTypeNames={allowedTypeNames}
            notes={notes}
          />
        </div>
      )}
    </div>
  );
}
