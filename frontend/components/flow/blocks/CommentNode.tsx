/**
 * Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
 * SPDX-License-Identifier: SUL-1.0
 */

import { NodeEditorRepresentation } from "@/generated/editor";
import { MultiLineTextPropertyEdit } from "./components/pads/property_edit/MultiLineTextPropertyEdit";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { usePropertyPad } from "./components/pads/hooks/usePropertyPad";

export interface CommentNodeProps {
  data: NodeEditorRepresentation;
}

export function CommentNode({ data }: CommentNodeProps) {
  const { runtimeValue } = usePropertyPad<string>(data.id, "text");
  return (
    <div className="min-w-80 w-[480px] flex flex-col bg-transparent rounded-lg relative text-white">
      <div className="h-2 bg-transparent rounded-t-lg drag-handle cursor-grab active:cursor-grabbing"></div>
      <div className="flex flex-col p-4">
        <div className="[&_.pad-handle]:hidden [&_.pad-label]:hidden [&_textarea]:min-h-[72px] [&_textarea]:bg-transparent [&_textarea]:text-white [&_textarea]:border-transparent [&_textarea]:placeholder:text-white/50 [&_textarea]:focus:border-transparent [&_textarea:hover]:bg-transparent">
          <MultiLineTextPropertyEdit nodeId={data.id} padId="text" />
        </div>
        <div className="mt-3 border-t border-base-300 pt-3">
          <div className="text-xs text-base-content/60 mb-2">Preview</div>
          <div className="markdown-body text-white break-words whitespace-pre-wrap">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>
              {runtimeValue || ""}
            </ReactMarkdown>
          </div>
        </div>
      </div>
    </div>
  );
}
