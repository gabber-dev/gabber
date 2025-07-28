/**
 * Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
 * SPDX-License-Identifier: SUL-1.0
 */

"use client";
import React, { useCallback } from "react";

import { RepositoryProvider } from "@/hooks/useRepository";
import { RepositoryApp, RepositorySubGraph } from "@/generated/repository";
import { AppList } from "@/components/home/AppList";
import { CreateAppModal } from "@/components/home/CreateAppModal";
import { listApps, listSubgraphs } from "@/lib/repository";

type Props = {
  initialApps: RepositoryApp[];
  initialSubGraphs: RepositorySubGraph[];
};

export function ClientPage({ initialApps, initialSubGraphs }: Props) {
  const listAppsImpl = useCallback(async () => {
    return listApps();
  }, []);
  const saveAppImpl = useCallback(
    async (params: { name: string; graph: any }) => {
      return {} as RepositoryApp;
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
      <AppList />
      {/* Modal */}
      <CreateAppModal />
    </RepositoryProvider>
  );
}
