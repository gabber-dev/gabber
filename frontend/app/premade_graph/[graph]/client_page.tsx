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
import toast from "react-hot-toast";

type Props = {
  initialSubGraph: RepositorySubGraph;
};
export function ClientPage({ initialSubGraph }: Props) {
  const saveImpl = useCallback(async () => {
    toast.error("Premade subgraphs can't be modified");
  }, []);

  const startRunImpl = useCallback(async () => {
    throw new Error("startRunImpl is not implemented for SubGraphEdit");
  }, []);

  return (
    <div className="absolute top-0 left-0 right-0 bottom-0">
      <EditorProvider
        debug={false}
        editor_url="ws://localhost:8000/ws"
        saveImpl={saveImpl}
        savedGraph={initialSubGraph.graph}
      >
        <RunProvider generateConnectionDetailsImpl={startRunImpl}>
          <SubGraphEdit editable={false} />
        </RunProvider>
      </EditorProvider>
    </div>
  );
}
