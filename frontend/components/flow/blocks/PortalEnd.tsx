/**
 * Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
 * SPDX-License-Identifier: SUL-1.0
 */

import {
  PadEditorRepresentation,
  PortalEnd as PortalEndModel,
} from "@/generated/editor";
import { Handle, Position } from "@xyflow/react";
import { DataTypeColor } from "./components/pads/utils/dataTypeColors";
import { useEditor } from "@/hooks/useEditor";

export interface BaseBlockProps {
  data: {
    portalEnd: PortalEndModel;
    dataColor: DataTypeColor;
    sourcePad: PadEditorRepresentation;
    sourcePortalId: string;
  };
}

export function PortalEnd({ data }: BaseBlockProps) {
  const { portalEnd, dataColor, sourcePortalId } = data;
  const { portalHighlights, highlightPortal } = useEditor();

  const isHighlighted = portalHighlights.portalEnds.has(portalEnd.id);

  return (
    <div
      className="w-8 h-8 rounded-full relative group"
      style={{ background: dataColor.background }}
      onMouseEnter={() => highlightPortal(sourcePortalId)}
      onMouseLeave={() => highlightPortal(undefined)}
    >
      {isHighlighted && (
        <div className="absolute inset-0 rounded-full border-dashed border-4 -left-2 -top-2 -bottom-2 -right-2 pointer-events-none transition-all duration-200 ease-in-out animate-[spin_3s_linear_infinite]" />
      )}
      <Handle
        id="source"
        type="source"
        position={Position.Right}
        className="transition-all duration-400 ease-in-out transform -translate-x-3 group-hover:translate-x-[55%] !m-0 !w-4 !h-4 !p-0 opacity-0 group-hover:opacity-100 border border-base-300 border-2"
        style={{
          borderRadius: "9999px",
          boxSizing: "border-box",
          margin: 0,
          padding: 0,
          background: dataColor.background,
        }}
      />
    </div>
  );
}
