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

type ConnectionState = "not_connected" | "connecting" | "connected";

type RunContextType = {
  connectionState: ConnectionState;
  stopRun: () => void;
  startRun: () => void;
};

const RunContext = createContext<RunContextType | undefined>(undefined);

interface RunProviderProps {
  children: React.ReactNode;
  startRunImpl: () => Promise<any>;
}

export function RunProvider({ children, startRunImpl }: RunProviderProps) {
  // const { selectedAppObject, selectedFlow, newestVersionObj } = useApp();

  const [connectionOpts, setConnectionOpts] = useState<any | null>(null);
  const [connectionDetailsLoading, setConnectionDetailsLoading] =
    useState(false);

  const connectionState: ConnectionState = useMemo(() => {
    if (connectionDetailsLoading) {
      return "connecting";
    }
    if (connectionOpts) {
      return "connected";
    }
    return "not_connected";
  }, [connectionOpts, connectionDetailsLoading]);

  const startRun = useCallback(async () => {
    if (connectionState !== "not_connected") {
      return;
    }

    setConnectionDetailsLoading(true);
    try {
      const res = await startRunImpl();

      setConnectionOpts({
        connection_details: res,
      });
    } catch (e) {
      toast.error("Failed to start run. Please try again.");
    } finally {
      setConnectionDetailsLoading(false);
    }
  }, [connectionState, startRunImpl]);

  const stopRun = useCallback(async () => {
    if (connectionState !== "connected") {
      return;
    }
    setConnectionOpts(null);
  }, [connectionState]);

  return (
    <RunContext.Provider
      value={{
        connectionState,
        stopRun,
        startRun,
      }}
    >
      <RealtimeSessionEngineProvider connectionOpts={connectionOpts as any}>
        {children as any}
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
