import { PadTriggeredValue, PropertyPad, SourcePad } from "@gabber/client";
import { useEngine, useEngineInternal } from "./useEngine";
import { useCallback, useEffect, useRef, useState } from "react";

type UsePropertyPadType<DataType extends PadTriggeredValue> = {
    currentValue: DataType | "loading";
}

export function usePropertyPad<DataType extends PadTriggeredValue>(nodeId: string, padId: string): UsePropertyPadType<DataType> {
    const { engineRef } = useEngineInternal();
    const { connectionState } = useEngine();
    const padRef = useRef(engineRef.current.getPropertyPad<DataType>(nodeId, padId));
    const [currentValue, setCurrentValue] = useState<DataType | "loading">("loading");
    const padLoadingRef = useRef(false);

    const loadPadValue = useCallback(async () => {
        if (padLoadingRef.current) return; // Prevent multiple calls
        padLoadingRef.current = true;
        try {
            const value = await padRef.current.getValue();
            setCurrentValue(value);
        } catch (error) {
            console.error("Failed to load pad value:", error);
            setCurrentValue("loading");
        } finally {
            padLoadingRef.current = false;
        }
    }, [padRef]);

    useEffect(() => {
        if (connectionState === "connected") {
            loadPadValue();
        }
    }, [connectionState, padRef]);

    return {
        currentValue,
    }
}