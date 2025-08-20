/**
 * Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
 * SPDX-License-Identifier: SUL-1.0
 */

import { NodeEditorRepresentation } from "@/generated/editor";
import { ChatBubbleLeftRightIcon } from "@heroicons/react/24/outline";
import { MultiLineTextPropertyEdit } from "./components/pads/property_edit/MultiLineTextPropertyEdit";

export interface CommentNodeProps {
  data: NodeEditorRepresentation;
}

export function CommentNode({ data }: CommentNodeProps) {
  return (
    <div className="min-w-80 w-full flex flex-col bg-base-200 rounded relative">
      <div className="flex items-center gap-1 py-1 px-2 drag-handle cursor-grab active:cursor-grabbing">
        <ChatBubbleLeftRightIcon className="h-4 w-4 text-gray-600" />
        <div className="text-xs text-gray-600 font-mono">{data.id}</div>
      </div>

      <div className="[&_.pad-handle]:hidden [&_.pad-label]:hidden [&_textarea]:min-h-[72px] [&_textarea]:bg-transparent">
        <MultiLineTextPropertyEdit nodeId={data.id} padId="text" />
      </div>
    </div>
  );
}
