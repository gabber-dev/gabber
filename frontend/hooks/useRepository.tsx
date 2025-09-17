/**
 * Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
 * SPDX-License-Identifier: SUL-1.0
 */

"use client";

import {
  AppExport,
  RepositoryApp,
  RepositorySubGraph,
  SaveAppRequest,
  SaveSubgraphRequest,
} from "@/generated/repository";
import React, { createContext, useCallback, useContext, useState } from "react";
import toast from "react-hot-toast";

type RepositoryContextType = {
  apps: RepositoryApp[];
  appsLoading: boolean;
  saveApp: (params: SaveAppRequest) => Promise<RepositoryApp>;
  deleteApp: (appId: string) => Promise<void>;
  refreshApps: () => Promise<void>;

  subGraphs: RepositorySubGraph[];
  subGraphsLoading: boolean;
  saveSubGraph: (params: SaveSubgraphRequest) => Promise<RepositorySubGraph>;
  deleteSubGraph: (subGraphId: string) => Promise<void>;
  refreshSubGraphs: () => Promise<void>;

  importApp(exp: AppExport): Promise<RepositoryApp>;
  exportApp(appId: string): Promise<AppExport>;

  subgraphEditPath: (id: string) => string;
  appEditPath: (id: string) => string;
  debugRunPath: (id: string) => string;

  examples: RepositoryApp[];
};

export const RepositoryContext = createContext<
  RepositoryContextType | undefined
>(undefined);

type Props = {
  children: React.ReactNode;

  initialApps: RepositoryApp[];
  listAppsImpl: () => Promise<RepositoryApp[]>;
  saveAppImpl: (params: SaveAppRequest) => Promise<RepositoryApp>;
  deleteAppImpl: (appId: string) => Promise<void>;

  initialSubGraphs: RepositorySubGraph[];
  saveSubGraphImpl: (
    params: SaveSubgraphRequest,
  ) => Promise<RepositorySubGraph>;
  listSubgraphsImpl: () => Promise<RepositorySubGraph[]>;
  deleteSubGraphImpl: (subGraphId: string) => Promise<void>;

  importAppImpl: (exp: AppExport) => Promise<RepositoryApp>;
  exportAppImpl: (appId: string) => Promise<AppExport>;

  subgraphEditPath: (id: string) => string;
  appEditPath: (id: string) => string;
  debugRunPath: (id: string) => string;

  examples: RepositoryApp[];
};

export function RepositoryProvider({
  children,
  initialApps,
  deleteAppImpl,
  listAppsImpl,
  saveAppImpl,

  initialSubGraphs,
  saveSubGraphImpl,
  listSubgraphsImpl,
  deleteSubGraphImpl,

  importAppImpl,
  exportAppImpl,

  subgraphEditPath,
  appEditPath,
  debugRunPath,

  examples,
}: Props) {
  const [apps, setApps] = useState<RepositoryApp[]>(initialApps);
  const [appsLoading, setAppsLoading] = useState<boolean>(false);

  const [subGraphs, setSubGraphs] =
    useState<RepositorySubGraph[]>(initialSubGraphs);
  const [subGraphsLoading, setSubGraphsLoading] = useState<boolean>(false);

  const refreshApps = useCallback(async () => {
    if (appsLoading) {
      return;
    }
    setAppsLoading(true);
    try {
      const response = await listAppsImpl();
      setApps(response);
    } catch (error) {
      console.error("Error loading apps:", error);
      toast.error("Failed to load apps. Please try again later.");
    } finally {
      setAppsLoading(false);
    }
  }, [appsLoading, listAppsImpl]);

  const saveApp = async (params: SaveAppRequest): Promise<RepositoryApp> => {
    try {
      const resp = await saveAppImpl(params);
      await refreshApps();
      return resp;
    } catch (error) {
      toast.error("Error creating app. Please refresh.");
      console.error("Error creating app:", error);
      throw error;
    }
  };

  const deleteApp = async (appId: string) => {
    try {
      await deleteAppImpl(appId);
      setApps((prev) => prev.filter((a) => a.id !== appId));
      await refreshApps();
      toast.success("App deleted successfully");
    } catch (error) {
      toast.error("Failed to delete app");
      console.error("Error deleting app:", error);
      await refreshApps();
    }
  };

  const refreshSubGraphs = useCallback(async () => {
    if (subGraphsLoading) {
      return;
    }
    setSubGraphsLoading(true);
    try {
      const response = await listSubgraphsImpl();
      setSubGraphs(response);
    } catch (error) {
      console.error("Error loading subgraphs:", error);
      toast.error("Failed to load subgraphs. Please try again later.");
    } finally {
      setSubGraphsLoading(false);
    }
  }, [subGraphsLoading, listSubgraphsImpl]);

  const saveSubGraph = async (
    params: SaveSubgraphRequest,
  ): Promise<RepositorySubGraph> => {
    try {
      const resp = await saveSubGraphImpl(params);
      await refreshSubGraphs();
      return resp;
    } catch (error) {
      toast.error("Error creating subgraph. Please refresh.");
      console.error("Error creating subgraph:", error);
      throw error;
    }
  };

  const deleteSubGraph = async (subGraphId: string) => {
    try {
      await deleteSubGraphImpl(subGraphId);
      setSubGraphs((prev) => prev.filter((sg) => sg.id !== subGraphId));
      await refreshSubGraphs();
      toast.success("Subgraph deleted successfully");
    } catch (error) {
      toast.error("Failed to delete subgraph");
      console.error("Error deleting subgraph:", error);
      await refreshSubGraphs();
    }
  };

  const importApp = async (exp: AppExport): Promise<RepositoryApp> => {
    try {
      const resp = await importAppImpl(exp);
      await refreshApps();
      toast.success("App imported successfully");
      return resp;
    } catch (error) {
      toast.error("Error importing app. Please refresh.");
      console.error("Error importing app:", error);
      throw error;
    }
  };

  const exportApp = async (appId: string): Promise<AppExport> => {
    try {
      const resp = await exportAppImpl(appId);
      return resp;
    } catch (error) {
      toast.error("Error exporting app. Please refresh.");
      console.error("Error exporting app:", error);
      throw error;
    }
  };

  return (
    <RepositoryContext.Provider
      value={{
        apps,
        appsLoading,
        refreshApps,
        saveApp,
        deleteApp,

        importApp,
        exportApp,

        subGraphs,
        subGraphsLoading,
        refreshSubGraphs,
        saveSubGraph,
        deleteSubGraph,

        subgraphEditPath,
        appEditPath,
        debugRunPath,

        examples,
      }}
    >
      {children}
    </RepositoryContext.Provider>
  );
}

export function useRepository() {
  const context = useContext(RepositoryContext);
  if (context === undefined) {
    throw new Error("useRepository must be used within a RepositoryProvider");
  }
  return context;
}
