/**
 * Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
 * SPDX-License-Identifier: SUL-1.0
 */

"use client";

import { EditorProvider } from "@/hooks/useEditor";
import { useCallback } from "react";
import { RunProvider } from "@/hooks/useRun";
import { AppRunConnectionDetails } from "@/generated/repository";
import { GraphEditorRepresentation } from "@/generated/editor";
import { DebugGraph } from "@/components/debug/DebugGraph";

type Props = {
  connectionDetails: AppRunConnectionDetails;
  graph: GraphEditorRepresentation;
};
export function ClientPage({ graph, connectionDetails }: Props) {
  const saveImpl = useCallback(async () => {
    throw new Error("saveImpl is not implemented for Debug mode");
  }, []);

  const startRunImpl = useCallback(async () => {
    return connectionDetails;
  }, [connectionDetails]);

  return (
    <div className="absolute top-0 left-0 right-0 bottom-0">
      <EditorProvider
        debug={true}
        editor_url="ws://localhost:8000/ws"
        saveImpl={saveImpl}
        savedGraph={graph}
      >
        <RunProvider startRunImpl={startRunImpl}>
          <DebugGraph />
        </RunProvider>
      </EditorProvider>
    </div>
  );
}
