/**
 * Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
 * SPDX-License-Identifier: SUL-1.0
 */

import { NodeEditorRepresentation } from "@/app/(authenticated)/project/[project_id]/apps/(generated)/editor_server";
import { useMemo } from "react";
import { ChatBubbleLeftRightIcon } from "@heroicons/react/24/outline";
import { PropertyPad } from "./components/pads/PropertyPad";

export interface CommentNodeProps {
  data: NodeEditorRepresentation;
}

export function CommentNode({ data }: CommentNodeProps) {
  const propertySinkPad = useMemo(() => {
    return data.pads.filter(
      (p) => p.type === "PropertySinkPad" || p.type === "MultiLineTextSinkPad",
    );
  }, [data]);

  return (
    <div className="min-w-80 min-h-48 w-full h-full flex flex-col bg-base-200 border-2 border-accent border-b-4 border-r-4 rounded-lg relative">
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

      <div className="flex flex-1 flex-col gap-3 p-4 nodrag cursor-default">
        {propertySinkPad.map((pad) => (
          <div key={pad.id}>
            <PropertyPad nodeId={data.id} data={pad} />
          </div>
        ))}
      </div>
    </div>
  );
}
