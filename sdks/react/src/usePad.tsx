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