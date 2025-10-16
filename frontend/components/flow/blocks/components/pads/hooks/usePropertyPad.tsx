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
import { useRun } from "@/hooks/useRun";
import toast from "react-hot-toast";

type Result<T> = {
  pad: PadEditorRepresentation | undefined;
  editorValue: T | undefined;
  singleAllowedType: BasePadType | undefined;
  runtimeValue: T | undefined;
  runtimeChanged: boolean;
  loadListItems?: () => Promise<void>;
  setEditorValue: (value: T) => void;
};

export function usePropertyPad<T>(nodeId: string, padId: string): Result<T> {
  const { editorRepresentation, updatePad } = useEditor();
  const { currentValue, loadListItems } = useRuntimePropertyPad(nodeId, padId);
  const { connectionState } = useRun();

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

      // Show toast warning if app is running
      const isRunning =
        connectionState === "connected" || connectionState === "connecting";
      if (isRunning) {
        toast.error(
          "Cannot edit properties while app is running. Stop the app to make changes.",
        );
        return;
      }

      updatePad({
        type: "update_pad",
        node: nodeId,
        pad: padId,
        value: value as Value,
      });
    },
    [nodeId, pad, padId, updatePad, connectionState],
  );

  const runtimeValue = useMemo(() => {
    if (currentValue === "loading") {
      return editorValue;
    }
    const cv = currentValue.value;
    if (cv !== editorValue) {
      if (currentValue.type === "list") {
        return currentValue as T;
      }
      return cv as T;
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
