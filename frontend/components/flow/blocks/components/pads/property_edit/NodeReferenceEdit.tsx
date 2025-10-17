/**
 * Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
 * SPDX-License-Identifier: SUL-1.0
 */

import { usePropertyPad } from "../hooks/usePropertyPad";
import { useEditor } from "@/hooks/useEditor";
import { PropertyEditProps } from "./PropertyEdit";
import { NodeReference } from "@gabber/client-react";

export function NodeReferenceEdit({ nodeId, padId }: PropertyEditProps) {
  const { runtimeValue } = usePropertyPad<NodeReference>(nodeId, padId);
  const { editorRepresentation } = useEditor();

  const selectedNode = editorRepresentation.nodes.find(
    (n) => n.id === runtimeValue?.node_id,
  );

  return (
    <div className="text-sm text-neutral-700 dark:text-neutral-300">
      <div>{selectedNode?.id}</div>
    </div>
  );
}
