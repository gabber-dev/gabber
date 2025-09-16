/**
 * Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
 * SPDX-License-Identifier: SUL-1.0
 */

import {
  BasePadType,
  PadEditorRepresentation,
  Value,
} from "@/generated/editor";
import { useCallback, useMemo } from "react";
import { usePropertyPad as useRuntimePropertyPad } from "@gabber/client-react";
import { useEditor } from "@/hooks/useEditor";

type Result<T> = {
  pad: PadEditorRepresentation | undefined;
  editorValue: T | undefined;
  singleAllowedType: BasePadType | undefined;
  runtimeValue: T | undefined;
  runtimeChanged: boolean;
  setEditorValue: (value: T) => void;
};

export function usePropertyPad<T>(nodeId: string, padId: string): Result<T> {
  const { editorRepresentation, updatePad } = useEditor();
  const { currentValue } = useRuntimePropertyPad(nodeId, padId);

  const node = editorRepresentation.nodes.find((n) => n.id === nodeId);
  const pad = node?.pads.find((p) => p.id === padId);
  const singleAllowedType = useMemo(() => {
    if (!pad) return undefined;
    if (pad.allowed_types?.length === 1) {
      return pad.allowed_types[0];
    }

    return undefined;
  }, [pad]);

  const editorValue = useMemo(() => {
    if (!pad) {
      return undefined;
    }
    if (pad.value === undefined) {
      return undefined;
    }
    return pad.value as T;
  }, [pad]);

  const setEditorValue = useCallback(
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

  const runtimeValue = useMemo(() => {
    if (currentValue === "loading") {
      return editorValue;
    }
    if (currentValue.value !== editorValue) {
      return currentValue.value as T;
    }
    return editorValue;
  }, [currentValue, editorValue]);

  const runtimeChanged = useMemo(() => {
    if (currentValue === "loading") {
      return false;
    }
    return currentValue.value !== editorValue;
  }, [currentValue, editorValue]);

  return {
    pad: pad as PadEditorRepresentation | undefined,
    editorValue,
    runtimeValue,
    runtimeChanged,
    singleAllowedType,
    setEditorValue,
  };
}
