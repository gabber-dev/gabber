/**
 * Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
 * SPDX-License-Identifier: SUL-1.0
 */

"use client";

import { TopBar } from "@/components/TopBar";
import {
  GraphEditorRepresentation,
  RepositoryApp,
  RepositorySubGraph,
} from "@/generated/repository";
import { RepositoryProvider } from "@/hooks/useRepository";
import { listApps, listSubgraphs, saveApp } from "@/lib/repository";
import { useCallback } from "react";
import { Toaster } from "react-hot-toast";
type Props = {
  initialApps: RepositoryApp[];
  initialSubGraphs: RepositorySubGraph[];
  children: React.ReactNode;
};
export function ClientLayout({
  children,
  initialApps,
  initialSubGraphs,
}: Props) {
  const listAppsImpl = useCallback(async () => {
    return listApps();
  }, []);
  const saveAppImpl = useCallback(
    async (params: { name: string; graph: GraphEditorRepresentation }) => {
      return await saveApp(params);
    },
    [],
  );
  const deleteAppImpl = useCallback(async (appId: string) => {}, []);

  const listSubgraphsImpl = useCallback(async () => {
    return listSubgraphs();
  }, []);

  const deleteSubGraphImpl = useCallback(async (subGraphId: string) => {}, []);

  return (
    <RepositoryProvider
      initialApps={initialApps}
      initialSubGraphs={initialSubGraphs}
      listAppsImpl={listAppsImpl}
      saveAppImpl={saveAppImpl}
      deleteAppImpl={deleteAppImpl}
      listSubgraphsImpl={listSubgraphsImpl}
      deleteSubGraphImpl={deleteSubGraphImpl}
    >
      <Toaster />
      <div className="absolute top-0 left-0 right-0 h-10">
        <TopBar />
      </div>
      <div className="absolute top-10 left-0 right-0 bottom-0 overflow-y-auto">
        {children}
      </div>
    </RepositoryProvider>
  );
}
