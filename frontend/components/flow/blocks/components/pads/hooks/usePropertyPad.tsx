/**
 * Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
 * SPDX-License-Identifier: SUL-1.0
 */

import {
  BasePadType,
  PadEditorRepresentation,
  Value,
} from "@/generated/editor";
import { useEditor } from "@/hooks/useEditor";
import { useCallback, useMemo } from "react";

type Result<T> = {
  pad: PadEditorRepresentation | undefined;
  value: T | undefined;
  singleAllowedType: BasePadType | undefined;
  setValue: (value: T) => void;
};

export function usePropertyPad<T>(nodeId: string, padId: string): Result<T> {
  const { editorRepresentation, updatePad } = useEditor();

  const node = editorRepresentation.nodes.find((n) => n.id === nodeId);
  const pad = node?.pads.find((p) => p.id === padId);
  const singleAllowedType = useMemo(() => {
    if (!pad) return undefined;
    if (pad.allowed_types?.length === 1) {
      return pad.allowed_types[0];
    }

    return undefined;
  }, [pad]);

  const value = useMemo(() => {
    if (!pad) {
      return undefined;
    }
    if (pad.value === undefined) {
      return undefined;
    }
    return pad.value as T;
  }, [pad]);

  const setValue = useCallback(
    (value: T) => {
      if (!pad || !nodeId) {
        console.warn(`Pad with id ${padId} not found in node ${nodeId}`);
        return;
      }
      updatePad({
        type: "update_pad",
        node: nodeId,
        pad: padId,
        value: value as Value,
      });
    },
    [nodeId, pad, padId, updatePad],
  );

  return {
    pad: pad as PadEditorRepresentation | undefined,
    value,
    singleAllowedType,
    setValue,
  };
}
