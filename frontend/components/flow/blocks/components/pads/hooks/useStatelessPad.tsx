/**
 * Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
 * SPDX-License-Identifier: SUL-1.0
 */

import { PadEditorRepresentation } from "@/app/(authenticated)/project/[project_id]/apps/(generated)/editor_server";
import { useEditor } from "@/app/(authenticated)/project/[project_id]/apps/(providers)/useEditor";
import { useNodeId } from "@xyflow/react";
import { useMemo } from "react";

type Result<T> = {
  pad: PadEditorRepresentation | undefined;
  singleAllowedType: Record<string, any> | undefined;
};

export function useStatelessPad<T>(padId: string): Result<T> {
  const nodeId = useNodeId();
  const { editorRepresentation } = useEditor();

  const node = editorRepresentation.nodes.find((n) => n.id === nodeId);
  const pad = node?.pads.find((p) => p.id === padId);
  const singleAllowedType = useMemo(() => {
    if (!pad) return undefined;
    if (pad.allowed_types?.length === 1) {
      return pad.allowed_types[0];
    }

    return undefined;
  }, [pad]);

  return {
    pad: pad as PadEditorRepresentation | undefined,
    singleAllowedType,
  };
}
