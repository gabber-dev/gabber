/**
 * Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 *
 * SPDX-License-Identifier: Apache-2.0
 */

import { Engine, EngineHandler, Publication, Subscription, RuntimeEventPayload_LogItem } from "@gabber/client"
import { LocalTrack } from "@gabber/client";
import { GetLocalTrackOptions } from "@gabber/client";
import { ConnectionDetails, PublishParams, SubscribeParams, ConnectionState } from "@gabber/client";
import { createContext, useContext, useRef, useState } from "react";

type EngineContextType = {
    connectionState: ConnectionState;
    getLocalTrack: (opts: GetLocalTrackOptions) => Promise<LocalTrack>;
    registerToolCallHandler: (toolName: string, handler: (args: any) => Promise<string>) => void;
    connect: (details: ConnectionDetails) => Promise<void>;
    disconnect: () => Promise<void>;
    publishToNode: (params: PublishParams) => Promise<Publication>;
    subscribeToNode: (params: SubscribeParams) => Promise<Subscription>;
    logItems: RuntimeEventPayload_LogItem[];
    clearLogItems: () => void;
};

type InternalEngineContextType = {
    engineRef: React.RefObject<Engine>;
};

export const EngineContext = createContext<({main: EngineContextType, internal: InternalEngineContextType}) | undefined>(undefined);

export function EngineProvider({ children, maxLogItems }: { children: React.ReactNode, maxLogItems?: number }) {
    const [connectionState, setConnectionState] = useState<ConnectionState>("disconnected");
    const [logItems, setLogItems] = useState<RuntimeEventPayload_LogItem[]>([]);

    const handlerRef = useRef<EngineHandler>(undefined);
    if (!handlerRef.current) {
        handlerRef.current = {
            onConnectionStateChange: (state) => {
                setConnectionState(state);
            },
            onLogItem: (item) => {
                setLogItems((items) => {
                    const newItems = [item, ...items];
                    if(newItems.length > (maxLogItems || 100)) {
                        newItems.splice(maxLogItems || 100);
                    }
                    return newItems;
                });
            }
        };
    }

    const engineRef = useRef<Engine>(undefined);
    if (!engineRef.current) {
        engineRef.current = new Engine({ handler: handlerRef.current });
    }

    return (
        <EngineContext.Provider value={{
            main: {
                connectionState,
                getLocalTrack: engineRef.current.getLocalTrack,
                connect: engineRef.current.connect,
                disconnect: engineRef.current.disconnect,
                publishToNode: engineRef.current.publishToNode,
                subscribeToNode: engineRef.current.subscribeToNode,
                registerToolCallHandler: engineRef.current.registerToolCallHandler,
                logItems,
                clearLogItems: () => setLogItems([]),
            },
            internal: {
                engineRef: engineRef as React.RefObject<Engine>
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