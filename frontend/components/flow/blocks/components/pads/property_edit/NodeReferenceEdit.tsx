/**
 * Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
 * SPDX-License-Identifier: SUL-1.0
 */

import { usePropertyPad } from "../hooks/usePropertyPad";
import { useEditor } from "@/hooks/useEditor";
import ReactModal from "react-modal";
import { PropertyEditProps } from "./PropertyEdit";

export function NodeReferenceEdit({ nodeId, padId }: PropertyEditProps) {
  const { value } = usePropertyPad(nodeId, padId);
  const { editorRepresentation } = useEditor();

  const selectedNode = editorRepresentation.nodes.find((n) => n.id === value);

  return (
    <div className="text-sm text-neutral-700 dark:text-neutral-300">
      <div ref={(el) => ReactModal.setAppElement(el as any)} />
      <div>{selectedNode?.id}</div>
    </div>
  );
}
