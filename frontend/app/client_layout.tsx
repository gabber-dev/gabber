/**
 * Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
 * SPDX-License-Identifier: SUL-1.0
 */

"use client";

import { TopBar } from "@/components/TopBar";
import {
  AppExport,
  RepositoryApp,
  RepositorySubGraph,
  SaveAppRequest,
  SaveSubgraphRequest,
} from "@/generated/repository";
import { RepositoryProvider } from "@/hooks/useRepository";
import {
  deleteApp,
  deleteSubGraph,
  exportApp,
  importApp,
  listApps,
  listSubGraphs,
  saveApp,
  saveSubGraph,
} from "@/lib/repository";
import { useCallback } from "react";
import { Toaster } from "react-hot-toast";
type Props = {
  initialApps: RepositoryApp[];
  initialSubGraphs: RepositorySubGraph[];
  examples: RepositoryApp[];
  children: React.ReactNode;
};
export function ClientLayout({
  children,
  initialApps,
  initialSubGraphs,
  examples: initialExamples,
}: Props) {
  const listAppsImpl = useCallback(async () => {
    return listApps();
  }, []);
  const saveAppImpl = useCallback(async (params: SaveAppRequest) => {
    return await saveApp(params);
  }, []);

  const deleteAppImpl = useCallback(async (appId: string) => {
    return await deleteApp(appId);
  }, []);

  const saveSubGraphImpl = useCallback(async (params: SaveSubgraphRequest) => {
    return await saveSubGraph(params);
  }, []);

  const listSubgraphsImpl = useCallback(async () => {
    return listSubGraphs();
  }, []);

  const deleteSubGraphImpl = useCallback(async (subGraphId: string) => {
    return await deleteSubGraph(subGraphId);
  }, []);

  const importAppImpl = useCallback(async (exp: AppExport) => {
    const res = await importApp(exp);
    return res;
  }, []);

  const exportAppImpl = useCallback(async (appId: string) => {
    const res = await exportApp(appId);
    return res;
  }, []);

  return (
    <RepositoryProvider
      initialApps={initialApps}
      initialSubGraphs={initialSubGraphs}
      listAppsImpl={listAppsImpl}
      saveAppImpl={saveAppImpl}
      deleteAppImpl={deleteAppImpl}
      listSubgraphsImpl={listSubgraphsImpl}
      saveSubGraphImpl={saveSubGraphImpl}
      deleteSubGraphImpl={deleteSubGraphImpl}
      importAppImpl={importAppImpl}
      exportAppImpl={exportAppImpl}
      examples={initialExamples}
      subgraphEditPath={(id: string) => `/graph/${id}`}
      appEditPath={(id: string) => `/app/${id}`}
      debugRunPath={(id: string) => `/debug/${id}`}
    >
      <Toaster />
      <div className="absolute top-0 left-0 right-0 h-[70px]">
        <TopBar />
      </div>
      <div className="absolute top-[70px] left-0 right-0 bottom-0 overflow-y-auto">
        {children}
      </div>
    </RepositoryProvider>
  );
}
