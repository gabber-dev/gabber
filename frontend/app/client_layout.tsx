/**
 * Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
 * SPDX-License-Identifier: SUL-1.0
 */

"use client";

import { TopBar } from "@/components/TopBar";
import {
  AppExport,
  PublicSecret,
  RepositoryApp,
  RepositorySubGraph,
  SaveAppRequest,
  SaveSubgraphRequest,
} from "@/generated/repository";
import { RepositoryProvider } from "@/hooks/useRepository";
import {
  addSecret,
  deleteApp,
  deleteSecret,
  deleteSubGraph,
  exportApp,
  importApp,
  listApps,
  listSecrets,
  listSubGraphs,
  saveApp,
  saveSubGraph,
  updateSecret,
} from "@/lib/repository";
import { useCallback } from "react";
import { Toaster } from "react-hot-toast";

type Props = {
  initialApps: RepositoryApp[];
  initialSubGraphs: RepositorySubGraph[];
  initialPremadeSubGraphs: RepositorySubGraph[];
  examples: RepositoryApp[];
  initialSecrets: PublicSecret[];
  children: React.ReactNode;
};
export function ClientLayout({
  children,
  initialApps,
  initialSubGraphs,
  initialPremadeSubGraphs,
  examples: initialExamples,
  initialSecrets,
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

  const listSecretsImpl = useCallback(async () => {
    return listSecrets();
  }, []);

  const addSecretImpl = useCallback(async (name: string, value: string) => {
    return await addSecret(name, value);
  }, []);

  const updateSecretImpl = useCallback(async (id: string, name: string, value: string) => {
    return await updateSecret(id, name, value);
  }, []);

  const deleteSecretImpl = useCallback(async (id: string) => {
    return await deleteSecret(id);
  }, []);

  // Determine if this is a local deployment to show the .secret file message
  // Local deployment is indicated by the absence of specific environment variables
  const isLocalDeployment =
    !process.env.REPOSITORY_HOST && !process.env.GABBER_PUBLIC_HOST;

  const storageDescription = isLocalDeployment
    ? "Secrets are stored in your configured .secret file. Make sure to keep this file secure and never commit it to version control."
    : null; // Hide the message for cloud deployments

  return (
    <RepositoryProvider
      initialApps={initialApps}
      initialSubGraphs={initialSubGraphs}
      initialPremadeSubGraphs={initialPremadeSubGraphs}
      listAppsImpl={listAppsImpl}
      saveAppImpl={saveAppImpl}
      deleteAppImpl={deleteAppImpl}
      listSubgraphsImpl={listSubgraphsImpl}
      saveSubGraphImpl={saveSubGraphImpl}
      deleteSubGraphImpl={deleteSubGraphImpl}
      importAppImpl={importAppImpl}
      exportAppImpl={exportAppImpl}
      examples={initialExamples}
      initialSecrets={initialSecrets}
      listSecretsImpl={listSecretsImpl}
      addSecretImpl={addSecretImpl}
      updateSecretImpl={updateSecretImpl}
      deleteSecretImpl={deleteSecretImpl}
      storageDescription={storageDescription}
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
