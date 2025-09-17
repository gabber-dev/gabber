/**
 * Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
 * SPDX-License-Identifier: SUL-1.0
 */

"use client";

import { EditorProvider } from "@/hooks/useEditor";
import { useCallback } from "react";
import { SubGraphEdit } from "@/components/subgraph/SubGraphEdit";
import { RunProvider } from "@/hooks/useRun";
import { RepositorySubGraph } from "@/generated/repository";
import { saveSubGraph } from "@/lib/repository";
import { GraphEditorRepresentation } from "@/generated/editor";

type Props = {
  initialSubGraph: RepositorySubGraph;
  editorUrl: string;
};
export function ClientPage({ initialSubGraph, editorUrl }: Props) {
  const saveImpl = useCallback(
    async (graph: GraphEditorRepresentation) => {
      saveSubGraph({
        id: initialSubGraph.id,
        name: initialSubGraph.name,
        graph,
      });
    },
    [initialSubGraph.id, initialSubGraph.name],
  );

  const startRunImpl = useCallback(async () => {
    throw new Error("startRunImpl is not implemented for SubGraphEdit");
  }, []);

  return (
    <div className="absolute top-0 left-0 right-0 bottom-0">
      <EditorProvider
        debug={false}
        editor_url={editorUrl}
        saveImpl={saveImpl}
        savedGraph={initialSubGraph.graph}
      >
        <RunProvider generateConnectionDetailsImpl={startRunImpl}>
          <SubGraphEdit editable={true} />
        </RunProvider>
      </EditorProvider>
    </div>
  );
}
