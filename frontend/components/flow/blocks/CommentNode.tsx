/**
 * Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
 * SPDX-License-Identifier: SUL-1.0
 */

import { NodeEditorRepresentation } from "@/generated/editor";
import { MultiLineTextPropertyEdit } from "./components/pads/property_edit/MultiLineTextPropertyEdit";

export interface CommentNodeProps {
  data: NodeEditorRepresentation;
}

export function CommentNode({ data }: CommentNodeProps) {
  return (
    <div className="min-w-80 w-full flex flex-col bg-base-100 rounded-lg relative">
      <div className="h-2 bg-warning/20 rounded-t-lg drag-handle cursor-grab active:cursor-grabbing"></div>
      <div className="flex flex-col p-4">
        <div className="[&_.pad-handle]:hidden [&_.pad-label]:hidden [&_textarea]:min-h-[72px] [&_textarea]:bg-base-100 [&_textarea]:text-warning [&_textarea]:border-transparent [&_textarea]:placeholder:text-warning/50 [&_textarea]:focus:border-transparent">
          <MultiLineTextPropertyEdit nodeId={data.id} padId="text" />
        </div>
      </div>
    </div>
  );
}
