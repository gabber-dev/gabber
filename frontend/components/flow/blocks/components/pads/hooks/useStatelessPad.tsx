/**
 * Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
 * SPDX-License-Identifier: SUL-1.0
 */

import { PadEditorRepresentation, PadType } from "@/generated/editor";
import { useEditor } from "@/hooks/useEditor";
import { useNodeId } from "@xyflow/react";
import { useMemo } from "react";

type Result = {
  pad: PadEditorRepresentation | undefined;
  singleAllowedType: PadType | undefined;
};

export function useStatelessPad(padId: string): Result {
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
