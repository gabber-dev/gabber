/**
 * Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
 * SPDX-License-Identifier: SUL-1.0
 */

import { PadEditorRepresentation, Portal } from "@/generated/editor";
import { Handle, Position } from "@xyflow/react";
import { DataTypeColor } from "./components/pads/utils/dataTypeColors";
import { PlusIcon } from "@heroicons/react/24/outline";
import { useEditor } from "@/hooks/useEditor";

export interface BaseBlockProps {
  data: {
    portal: Portal;
    dataColor: DataTypeColor;
    sourcePad: PadEditorRepresentation;
  };
}
// export interface CreatePortalEndEdit {
//   type?: Type10;
//   portal_id: PortalId;
//   editor_position: EditorPosition4;
//   [k: string]: unknown;
// }

export function PortalStart({ data }: BaseBlockProps) {
  const { portal, dataColor, sourcePad } = data;
  const { createPortalEnd } = useEditor();
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
      <div className="absolute left-full ml-2 top-1/2 -translate-y-1/2 opacity-0 group-hover:opacity-100 transition-opacity duration-200 ease-in-out">
        <button
          onClick={() => {
            createPortalEnd({
              type: "create_portal_end",
              portal_id: portal.id,
              editor_position: [
                (portal.editor_position[0] as number) + 40,
                (portal.editor_position[1] as number) + 40,
              ],
            });
          }}
          className="btn btn-primary w-6 h-6 p-0 m-0 flex items-center justify-center rounded-full"
        >
          <PlusIcon className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
}
