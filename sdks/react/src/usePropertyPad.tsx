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

import { PadValue, PropertyPad } from "@gabber/client";
import { useEngine, useEngineInternal } from "./useEngine";
import { useCallback, useEffect, useRef, useState } from "react";
import { usePad } from "./usePad";
import { ConnectionState } from "@gabber/client";

type UsePropertyPadType<DataType extends PadValue> = {
    currentValue: DataType | "loading";
}

export function usePropertyPad<DataType extends PadValue>(nodeId: string, padId: string): UsePropertyPadType<DataType> {
    const { engineRef } = useEngineInternal();
    const { connectionState } = useEngine();
    const padRef = useRef<PropertyPad<DataType>>(undefined);
    if (!padRef.current) {
        padRef.current = engineRef.current.getPropertyPad<DataType>(nodeId, padId);
    }
    const [currentValue, setCurrentValue] = useState<DataType | "loading">("loading");
    const padLoadingRef = useRef(false);
    const prevConnectionState = useRef<ConnectionState>("disconnected");
    const { lastValue } = usePad<DataType>(nodeId, padId);

    const loadPadValue = useCallback(async () => {
        if (padLoadingRef.current) return; // Prevent multiple calls
        padLoadingRef.current = true;
        try {
            const value = (await padRef.current!.getValue()) as DataType;
            setCurrentValue(value);
        } catch (error) {
            console.error("Failed to load pad value:", error);
            setCurrentValue("loading");
        } finally {
            padLoadingRef.current = false;
        }
    }, [padRef]);

    useEffect(() => {
        if (connectionState === "connected" && prevConnectionState.current !== "connected") {
            loadPadValue();
        }
        prevConnectionState.current = connectionState;
    }, [connectionState, loadPadValue]);


    useEffect(() => {
        if (lastValue && connectionState === "connected") {
            setCurrentValue(lastValue as DataType);
        } else if(connectionState !== "connected") {
            setCurrentValue("loading");
        }
    }, [lastValue, connectionState]);

    return {
        currentValue,
    }
}