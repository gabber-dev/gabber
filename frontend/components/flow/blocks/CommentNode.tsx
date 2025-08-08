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
    <div className="min-w-80 w-full flex flex-col bg-base-200 border-2 border-accent border-b-4 border-r-4 rounded-lg relative">
      <div className="flex w-full items-center gap-2 bg-base-300 border-b-2 border-accent p-3 rounded-t-lg drag-handle cursor-grab active:cursor-grabbing">
        <ChatBubbleLeftRightIcon className="h-5 w-5 text-accent" />
        <div className="flex-1">
          <h2 className="text-lg text-primary font-medium">
            {data.editor_name}
          </h2>
          <div className="text-xs text-base-content/60 font-mono">
            {data.id}
          </div>
        </div>
      </div>

      <div className="flex flex-col p-4">
        <div className="[&_.pad-handle]:hidden [&_.pad-label]:hidden [&_textarea]:min-h-[72px]">
          <MultiLineTextPropertyEdit nodeId={data.id} padId="text" />
        </div>
      </div>
    </div>
  );
}
