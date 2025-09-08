/**
 * Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
 * SPDX-License-Identifier: SUL-1.0
 */

import { NodeEditorRepresentation } from "@/generated/editor";
import { MultiLineTextPropertyEdit } from "./components/pads/property_edit/MultiLineTextPropertyEdit";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { usePropertyPad } from "./components/pads/hooks/usePropertyPad";
import { useEffect, useRef, useState } from "react";

export interface CommentNodeProps {
  data: NodeEditorRepresentation;
}

export function CommentNode({ data }: CommentNodeProps) {
  const { runtimeValue } = usePropertyPad<string>(data.id, "text");
  const [width, setWidth] = useState<number>(480);
  const startXRef = useRef<number | null>(null);
  const startWidthRef = useRef<number>(width);

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (startXRef.current === null) return;
      const delta = e.clientX - startXRef.current;
      const next = Math.max(320, Math.min(960, startWidthRef.current + delta));
      setWidth(next);
    };
    const handleMouseUp = () => {
      startXRef.current = null;
    };
    window.addEventListener("mousemove", handleMouseMove);
    window.addEventListener("mouseup", handleMouseUp);
    return () => {
      window.removeEventListener("mousemove", handleMouseMove);
      window.removeEventListener("mouseup", handleMouseUp);
    };
  }, []);

  const onResizeMouseDown = (e: React.MouseEvent<HTMLDivElement>) => {
    e.stopPropagation();
    startXRef.current = e.clientX;
    startWidthRef.current = width;
  };

  return (
    <div
      className="comment-node min-w-80 flex flex-col bg-transparent rounded-lg relative text-white"
      style={{ width: `${width}px` }}
      tabIndex={0}
    >
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
        <div
          className="absolute top-0 right-0 h-full w-2 cursor-ew-resize nodrag"
          onMouseDown={onResizeMouseDown}
        />
      </div>
    </div>
  );
}
