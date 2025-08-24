/**
 * Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
 * SPDX-License-Identifier: SUL-1.0
 */

"use client";

import { useCallback } from "react";
import { AppEditPage } from "@/components/app_edit/AppEditPage";
import { EditorProvider } from "@/hooks/useEditor";
import { RunProvider } from "@/hooks/useRun";
import { RepositoryApp } from "@/generated/repository";
import toast from "react-hot-toast";
import { createAppRun } from "@/lib/repository";
import { GraphEditorRepresentation } from "@/generated/editor";

type Props = {
  existingExample: RepositoryApp;
};

export function ClientPage({ existingExample: existingApp }: Props) {
  const saveImpl = useCallback(async () => {
    toast.error("Examples can't be saved. Please try again.");
  }, []);

  const startRunImpl = useCallback(
    async (params: { graph: GraphEditorRepresentation }) => {
      const resp = await createAppRun({ graph: params.graph });
      const connDetails = resp.connection_details;
      return connDetails;
    },
    [],
  );

  return (
    <div className="realtive w-full h-full">
      <div className="absolute top-0 left-0 right-0 bottom-0">
        <EditorProvider
          editor_url="ws://192.168.1.29:8000/ws"
          savedGraph={existingApp.graph}
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
