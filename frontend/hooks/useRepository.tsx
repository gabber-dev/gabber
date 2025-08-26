/**
 * Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
 * SPDX-License-Identifier: SUL-1.0
 */

"use client";

import {
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
  forceRefreshApps: () => Promise<void>;

  subGraphs: RepositorySubGraph[];
  subGraphsLoading: boolean;
  saveSubGraph: (params: SaveSubgraphRequest) => Promise<RepositorySubGraph>;
  deleteSubGraph: (subGraphId: string) => Promise<void>;
  refreshSubGraphs: () => Promise<void>;
  forceRefreshSubGraphs: () => Promise<void>;

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

  examples,
}: Props) {
  const [apps, setApps] = useState<RepositoryApp[]>(initialApps);
  const [appsLoading, setAppsLoading] = useState<boolean>(true);

  const [subGraphs, setSubGraphs] =
    useState<RepositorySubGraph[]>(initialSubGraphs);
  const [subGraphsLoading, setSubGraphsLoading] = useState<boolean>(true);

  const refreshApps = useCallback(async () => {
    if (appsLoading) {
      return;
    }
    setAppsLoading(true);
    try {
      const response = await listAppsImpl();
      setApps(response);
    } catch (error) {
      toast.error("Failed to load apps. Please try again later.");
    } finally {
      setAppsLoading(false);
    }
  }, [appsLoading, listAppsImpl]);

  const forceRefreshApps = useCallback(async () => {
    setAppsLoading(true);
    try {
      const response = await listAppsImpl();
      setApps(response);
    } catch (error) {
      toast.error("Failed to load apps. Please try again later.");
    } finally {
      setAppsLoading(false);
    }
  }, [listAppsImpl]);

  const saveApp = async (params: SaveAppRequest): Promise<RepositoryApp> => {
    try {
      const resp = await saveAppImpl(params);
      await forceRefreshApps();
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
      await forceRefreshApps();
      toast.success("App deleted successfully");
    } catch (error) {
      toast.error("Failed to delete app");
      console.error("Error deleting app:", error);
      await forceRefreshApps();
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
      toast.error("Failed to load subgraphs. Please try again later.");
    } finally {
      setSubGraphsLoading(false);
    }
  }, [subGraphsLoading, listSubgraphsImpl]);

  const forceRefreshSubGraphs = useCallback(async () => {
    setSubGraphsLoading(true);
    try {
      const response = await listSubgraphsImpl();
      setSubGraphs(response);
    } catch (error) {
      toast.error("Failed to load subgraphs. Please try again later.");
    } finally {
      setSubGraphsLoading(false);
    }
  }, [listSubgraphsImpl]);

  const saveSubGraph = async (
    params: SaveSubgraphRequest,
  ): Promise<RepositorySubGraph> => {
    try {
      const resp = await saveSubGraphImpl(params);
      await forceRefreshSubGraphs();
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
      await forceRefreshSubGraphs();
      toast.success("Subgraph deleted successfully");
    } catch (error) {
      toast.error("Failed to delete subgraph");
      console.error("Error deleting subgraph:", error);
      await forceRefreshSubGraphs();
    }
  };

  return (
    <RepositoryContext.Provider
      value={{
        apps,
        appsLoading,
        refreshApps,
        forceRefreshApps,
        saveApp: saveApp,
        deleteApp,

        subGraphs,
        subGraphsLoading,
        refreshSubGraphs,
        forceRefreshSubGraphs,
        saveSubGraph,
        deleteSubGraph,

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
