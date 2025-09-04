/**
 * Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
 * SPDX-License-Identifier: SUL-1.0
 */

import { PadEditorRepresentation, Portal } from "@/generated/editor";
import { Handle, Position } from "@xyflow/react";
import { DataTypeColor } from "./components/pads/utils/dataTypeColors";

export interface BaseBlockProps {
  data: {
    portal: Portal;
    dataColor: DataTypeColor;
    sourcePad: PadEditorRepresentation;
  };
}

export function PortalEnd({ data }: BaseBlockProps) {
  const { portal, dataColor, sourcePad } = data;
  return (
    <div
      className="w-8 h-8 rounded-full relative group"
      style={{
        background: dataColor.background,
      }}
    >
      <Handle
        id={"target"}
        type="target"
        position={Position.Left}
        style={{
          borderRadius: "9999px",
          boxSizing: "border-box",
          margin: 0,
          padding: 0,
          transform: "translate(0%, -50%)",
          background: "transparent",
          opacity: 1,
        }}
      />
    </div>
  );
}
