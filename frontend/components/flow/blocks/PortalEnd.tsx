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
      style={
        {
          background: dataColor.background,
          "--node-color": dataColor.background,
        } as React.CSSProperties
      }
    >
      <Handle
        id={"source"}
        type="source"
        position={Position.Right}
        className="transition-all duration-200 ease-in-out transform -translate-x-3 group-hover:translate-x-[60%] !m-0 !w-3 !h-3 !p-0 opacity-0 group-hover:opacity-100"
        style={{
          borderRadius: "9999px",
          boxSizing: "border-box",
          margin: 0,
          padding: 0,
          border: "none",
          background: dataColor.background,
        }}
      />
    </div>
  );
}
