import { PadTriggeredValue, SourcePad } from "@gabber/client";
import { useEngineInternal } from "./useEngine";
import { useEffect, useRef, useState } from "react";

type UsePadType = {
    lastValue: PadTriggeredValue | undefined;
}

export function usePad<DataType extends PadTriggeredValue>(nodeId: string, padId: string): UsePadType {
    const [lastValue, setLastValue] = useState<DataType | undefined>(undefined);
    const { engineRef } = useEngineInternal();
    const padRef = useRef<SourcePad<DataType> | undefined>(undefined);
    const padHandlerRef = useRef<(value: DataType) => void | undefined>(undefined);

    useEffect(() => {
        if(!padRef.current) {
            padRef.current = engineRef.current.getSourcePad<DataType>(nodeId, padId);
            padHandlerRef.current = (value: DataType) => {
                setLastValue(value);
            }
        }
        padRef.current!.on('value', padHandlerRef.current!);
        return () => {
            padRef.current!.off('value', padHandlerRef.current!);
            padRef.current!.destroy();
            padRef.current = undefined;
            padHandlerRef.current = undefined;
            setLastValue(undefined);
        };
    }, []);

    return {
        lastValue,
    }
}