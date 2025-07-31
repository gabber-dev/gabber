/**
 * Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
 * SPDX-License-Identifier: SUL-1.0
 */

"use client";

import React, {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useState,
} from "react";
import toast from "react-hot-toast";
import { RealtimeSessionEngineProvider } from "gabber-client-react";
import { GraphEditorRepresentation } from "@/generated/editor";
import { AppRunConnectionDetails } from "@/generated/repository";

type ConnectionState = "not_connected" | "connecting" | "connected";

type RunContextType = {
  connectionState: ConnectionState;
  stopRun: () => void;
  startRun: (params: { graph: GraphEditorRepresentation }) => void;
};

const RunContext = createContext<RunContextType | undefined>(undefined);

interface RunProviderProps {
  children: React.ReactNode;
  startRunImpl: (params: {
    graph: GraphEditorRepresentation;
  }) => Promise<AppRunConnectionDetails>;
}

export function RunProvider({ children, startRunImpl }: RunProviderProps) {
  // const { selectedAppObject, selectedFlow, newestVersionObj } = useApp();

  const [connectionDetails, setConnectionDetails] =
    useState<AppRunConnectionDetails | null>(null);
  const [connectionDetailsLoading, setConnectionDetailsLoading] =
    useState(false);

  const connectionState: ConnectionState = useMemo(() => {
    if (connectionDetailsLoading) {
      return "connecting";
    }
    if (connectionDetails) {
      return "connected";
    }
    return "not_connected";
  }, [connectionDetails, connectionDetailsLoading]);

  const startRun = useCallback(
    async (params: { graph: GraphEditorRepresentation }) => {
      if (connectionState !== "not_connected") {
        return;
      }

      setConnectionDetailsLoading(true);
      try {
        const res = await startRunImpl({ graph: params.graph });
        setConnectionDetails(res);
      } catch (e) {
        console.error("Failed to start run:", e);
        toast.error("Failed to start run. Please try again.");
      } finally {
        setConnectionDetailsLoading(false);
      }
    },
    [connectionState, startRunImpl],
  );

  const stopRun = useCallback(async () => {
    if (connectionState !== "connected") {
      return;
    }
    setConnectionDetails(null);
  }, [connectionState]);

  return (
    <RunContext.Provider
      value={{
        connectionState,
        stopRun,
        startRun,
      }}
    >
      <RealtimeSessionEngineProvider
        connectionOpts={
          connectionDetails ? { connection_details: connectionDetails } : null
        }
      >
        {children}
      </RealtimeSessionEngineProvider>
    </RunContext.Provider>
  );
}

export function useRun() {
  const context = useContext(RunContext);
  if (context === undefined) {
    throw new Error("useRun must be used within a RunProvider");
  }
  return context;
}
