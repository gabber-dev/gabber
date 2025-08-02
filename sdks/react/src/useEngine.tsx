import { Engine, EngineHandler, Publication, Subscription } from "@gabber/client"
import { ConnectionDetails, PublishParams, SubscribeParams, ConnectionState } from "@gabber/client";
import { createContext, useCallback, useContext, useRef, useState } from "react";

type EngineContextType = {
    connectionState: ConnectionState;
    connect: (details: ConnectionDetails) => Promise<void>;
    disconnect: () => Promise<void>;
    publishToNode: (params: PublishParams) => Promise<Publication>;
    subscribeToNode: (params: SubscribeParams) => Promise<Subscription>;
};

type InternalEngineContextType = {
    engineRef: React.RefObject<Engine>;
};

export const EngineContext = createContext<({main: EngineContextType, internal: InternalEngineContextType}) | undefined>(undefined);

export function EngineProvider({ children }: { children: React.ReactNode }) {
    const [connectionState, setConnectionState] = useState<ConnectionState>("disconnected");

    const handlerRef = useRef<EngineHandler>({
        onConnectionStateChange: (state) => {
            setConnectionState(state);
        }
    });

    const engineRef = useRef<Engine>(new Engine({ handler: handlerRef.current }));

    return (
        <EngineContext.Provider value={{
            main: {
                connectionState,
                connect: engineRef.current.connect,
                disconnect: engineRef.current.disconnect,
                publishToNode: engineRef.current.publishToNode,
                subscribeToNode: engineRef.current.subscribeToNode,
            },
            internal: {
                engineRef
            }
        }}>
            {children}
        </EngineContext.Provider>
    )
}

export function useEngine(): EngineContextType {
  const context = useContext(EngineContext);
  if (!context) {
    throw new Error("useEngine must be used within an EngineProvider");
  }
  return context.main;
}


export function useEngineInternal(): InternalEngineContextType {
  const context = useContext(EngineContext);
  if (!context) {
    throw new Error("useEngineInternal must be used within an EngineProvider");
  }
  return context.internal;
}