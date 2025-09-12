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
  runId: string | null;
  stopRun: () => void;
  startRun: (params: { graph: GraphEditorRepresentation }) => void;
};

const RunContext = createContext<RunContextType | undefined>(undefined);

type GenerateConnectionDetails = (params: {
  graph: GraphEditorRepresentation;
}) => Promise<{ connectionDetails: ConnectionDetails; runId: string }>;

interface RunProviderProps {
  children: React.ReactNode;
  generateConnectionDetailsImpl: GenerateConnectionDetails;
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
  generateConnectionDetailsImpl: GenerateConnectionDetails;
}) {
  const { connect, disconnect, connectionState } = useEngine();
  const [runId, setRunId] = useState<string | null>(null);
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
        setRunId(res.runId);
        await connect(res.connectionDetails);
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
    setRunId(null);
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
        runId,
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
