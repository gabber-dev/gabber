import { PadTriggeredValue, PropertyPad } from "@gabber/client";
import { useEngine, useEngineInternal } from "./useEngine";
import { useCallback, useEffect, useRef, useState } from "react";
import { usePad } from "./usePad";
import { ConnectionState } from "@gabber/client";

type UsePropertyPadType<DataType extends PadTriggeredValue> = {
    currentValue: DataType | "loading";
}

export function usePropertyPad<DataType extends PadTriggeredValue>(nodeId: string, padId: string): UsePropertyPadType<DataType> {
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
            const value = await padRef.current!.getValue();
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