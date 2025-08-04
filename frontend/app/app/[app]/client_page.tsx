/**
 * Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
 * SPDX-License-Identifier: SUL-1.0
 */

"use client";

import { useCallback, useState } from "react";
import { AppEditPage } from "@/components/app_edit/AppEditPage";
import { EditorProvider } from "@/hooks/useEditor";
import { RunProvider } from "@/hooks/useRun";
import { GraphEditorRepresentation } from "@/generated/editor";
import { useRepository } from "@/hooks/useRepository";
import { RepositoryApp } from "@/generated/repository";
import { createAppRun } from "@/lib/repository";

type Props = {
  existingApp: RepositoryApp;
};

export function ClientPage({ existingApp }: Props) {
  const { saveApp } = useRepository();
  const [savedGraph, setSavedGraph] = useState<GraphEditorRepresentation>(
    existingApp.graph as GraphEditorRepresentation,
  );

  const saveImpl = useCallback(
    async (graph: GraphEditorRepresentation) => {
      await saveApp({
        id: existingApp.id,
        name: existingApp.name,
        graph,
      });
      setSavedGraph(graph);
    },
    [existingApp.id, existingApp.name, saveApp],
  );

  const startRunImpl = useCallback(
    async (params: { graph: GraphEditorRepresentation }) => {
      const resp = await createAppRun({ graph: params.graph });
      return resp.connection_details;
    },
    [],
  );

  return (
    <div className="realtive w-full h-full">
      <div className="absolute top-0 left-0 right-0 bottom-0">
        <EditorProvider
          debug={false}
          editor_url="ws://localhost:8000/ws"
          savedGraph={savedGraph}
          saveImpl={saveImpl}
        >
          <RunProvider generateConnectionDetailsImpl={startRunImpl}>
            <AppEditPage />
          </RunProvider>
        </EditorProvider>
      </div>
    </div>
  );
}
