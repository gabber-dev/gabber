import { PadTriggeredValue, SourcePad } from "@gabber/client";
import { useEngineInternal } from "./useEngine";
import { useEffect, useRef, useState } from "react";

type UseSourcePadType = {
    lastValue: PadTriggeredValue | undefined;
}

export function useSourcePad<DataType extends PadTriggeredValue>(nodeId: string, padId: string): UseSourcePadType {
    const [lastValue, setLastValue] = useState<DataType | undefined>(undefined);
    const { engineRef } = useEngineInternal();
    const padRef = useRef<SourcePad<DataType>>(engineRef.current.getSourcePad<DataType>(nodeId, padId));
    const padHandlerRef = useRef((value: DataType) => {
        setLastValue(value);
    });

    useEffect(() => {
        padRef.current.on('value', padHandlerRef.current);
        return () => {
            padRef.current.off('value', padHandlerRef.current);
        };
    }, [padRef]);

    return {
        lastValue,
    }
}