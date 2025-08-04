import { PadTriggeredValue, SourcePad } from "@gabber/client";
import { useEngineInternal } from "./useEngine";
import { useCallback, useEffect, useRef, useState } from "react";
import { usePad } from "./usePad";

type UseSourcePadType<DataType extends PadTriggeredValue> = {
    pushValue: (v: DataType) => Promise<void>;
}

export function useSourcePad<DataType extends PadTriggeredValue>(nodeId: string, padId: string): UseSourcePadType<DataType> {
    const { engineRef } = useEngineInternal();
    const padRef = useRef<SourcePad<DataType>>(engineRef.current.getSourcePad<DataType>(nodeId, padId));

    const pushValue = useCallback(async (v: DataType) => {
        await padRef.current.pushValue(v);
    }, [engineRef, nodeId, padId]);

    return {
        pushValue,
    }
}