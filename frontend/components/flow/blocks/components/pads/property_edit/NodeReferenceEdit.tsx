/**
 * Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
 * SPDX-License-Identifier: SUL-1.0
 */

import { usePropertyPad } from "../hooks/usePropertyPad";
import { useEditor } from "@/hooks/useEditor";
import { PropertyEditProps } from "./PropertyEdit";

export function NodeReferenceEdit({ nodeId, padId }: PropertyEditProps) {
  const { runtimeValue } = usePropertyPad(nodeId, padId);
  const { editorRepresentation } = useEditor();

  const selectedNode = editorRepresentation.nodes.find(
    (n) => n.id === runtimeValue,
  );

  return (
    <div className="text-sm text-neutral-700 dark:text-neutral-300">
      <div>{selectedNode?.id}</div>
    </div>
  );
}
