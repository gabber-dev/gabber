/**
 * Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
 * SPDX-License-Identifier: SUL-1.0
 */

"use client";
import React, { useCallback, useState } from "react";

import { RepositoryProvider } from "@/hooks/useRepository";
import {
  GraphEditorRepresentation,
  RepositoryApp,
  RepositorySubGraph,
} from "@/generated/repository";
import { AppList } from "@/components/home/AppList";
import { CreateAppModal } from "@/components/home/CreateAppModal";
import { listApps, listSubgraphs, saveApp } from "@/lib/repository";
import ReactModal from "react-modal";

type Props = {
  initialApps: RepositoryApp[];
  initialSubGraphs: RepositorySubGraph[];
};

export function ClientPage({ initialApps, initialSubGraphs }: Props) {
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
      <div className="h-full w-full p-2">
        <AppList />
      </div>
    </RepositoryProvider>
  );
}
