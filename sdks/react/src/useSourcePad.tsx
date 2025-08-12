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
import { useCallback, useEffect, useRef, useState } from "react";

type UseSourcePadType<DataType extends PadTriggeredValue> = {
    pushValue: (v: DataType) => Promise<void>;
}

export function useSourcePad<DataType extends PadTriggeredValue>(nodeId: string, padId: string): UseSourcePadType<DataType> {
    const { engineRef } = useEngineInternal();
    const padRef = useRef<SourcePad<DataType> | undefined>(undefined);
    if (!padRef.current) {
        padRef.current = engineRef.current.getSourcePad<DataType>(nodeId, padId);
    }

    const pushValue = useCallback(async (v: DataType) => {
        await padRef.current!.pushValue(v);
    }, [engineRef, nodeId, padId]);

    return {
        pushValue,
    }
}