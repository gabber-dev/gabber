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
  useRef,
  useState,
} from "react";
import toast from "react-hot-toast";
import { GraphEditorRepresentation } from "@/generated/editor";
import {
  ConnectionDetails,
  ConnectionState,
  EngineProvider,
  useEngine,
} from "@gabber/client-react";

type RunContextType = {
  connectionState: ConnectionState;
  stopRun: () => void;
  startRun: (params: { graph: GraphEditorRepresentation }) => void;
};

const RunContext = createContext<RunContextType | undefined>(undefined);

interface RunProviderProps {
  children: React.ReactNode;
  generateConnectionDetailsImpl: (params: {
    graph: GraphEditorRepresentation;
  }) => Promise<ConnectionDetails>;
}

export function RunProvider({
  children,
  generateConnectionDetailsImpl,
}: RunProviderProps) {
  return (
    <EngineProvider>
      <Inner generateConnectionDetailsImpl={generateConnectionDetailsImpl}>
        {children}
      </Inner>
    </EngineProvider>
  );
}

function Inner({
  generateConnectionDetailsImpl,
  children,
}: {
  children?: React.ReactNode;
  generateConnectionDetailsImpl: (params: {
    graph: GraphEditorRepresentation;
  }) => Promise<ConnectionDetails>;
}) {
  const { connect, disconnect, connectionState } = useEngine();
  const [starting, setStarting] = useState(false);
  const startingRef = useRef(false);

  const startRun = useCallback(
    async (params: { graph: GraphEditorRepresentation }) => {
      if (startingRef.current) {
        console.warn("Run is already starting, ignoring new start request.");
        return;
      }
      startingRef.current = true;
      setStarting(true);
      try {
        const res = await generateConnectionDetailsImpl({
          graph: params.graph,
        });
        await connect(res);
      } catch (e) {
        console.error("Failed to start run:", e);
        toast.error("Failed to start run. Please try again.");
      }
      setStarting(false);
      startingRef.current = false;
    },
    [connect, generateConnectionDetailsImpl],
  );

  const stopRun = useCallback(async () => {
    await disconnect();
  }, [disconnect]);

  const resolvedConnectionState: ConnectionState = useMemo(() => {
    if (starting) {
      return "connecting";
    }
    return connectionState;
  }, [connectionState, starting]);

  return (
    <RunContext.Provider
      value={{
        connectionState: resolvedConnectionState,
        stopRun,
        startRun,
      }}
    >
      {children}
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
