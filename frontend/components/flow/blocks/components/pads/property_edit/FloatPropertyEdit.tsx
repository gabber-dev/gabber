/**
 * Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
 * SPDX-License-Identifier: SUL-1.0
 */

import { useState, useEffect } from "react";
import { usePropertyPad } from "../hooks/usePropertyPad";
import { PropertyEditProps } from "./PropertyEdit";

export function FloatPropertyEdit({ nodeId, padId }: PropertyEditProps) {
  const { runtimeValue, setEditorValue: setValue } = usePropertyPad<number>(
    nodeId,
    padId,
  );

  const [localValue, setLocalValue] = useState(runtimeValue?.toString() || "0");

  useEffect(() => {
    setLocalValue(runtimeValue?.toString() || "0");
  }, [runtimeValue]);

  const handleChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setLocalValue(event.target.value);
  };

  const handleBlur = () => {
    const numValue = parseFloat(localValue);
    setValue(isNaN(numValue) ? 0 : numValue);
  };

  return (
    <input
      type="number"
      step="0.01"
      value={localValue}
      onChange={handleChange}
      onBlur={handleBlur}
      placeholder="Enter number..."
      className="input input-bordered w-full bg-base-300 border-2 border-black border-b-4 border-r-4 rounded-lg text-base-content placeholder-base-content/40 focus:border-primary focus:ring-2 focus:ring-primary font-vt323 text-sm hover:bg-base-100 transition-colors duration-150"
    />
  );
}
