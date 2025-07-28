/**
 * Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
 * SPDX-License-Identifier: SUL-1.0
 */

import { usePropertyPad } from "../hooks/usePropertyPad";
import { PropertyEditProps } from "./PropertyEdit";

export function IntPropertyEdit({ nodeId, padId }: PropertyEditProps) {
  const { value, setValue } = usePropertyPad<number>(nodeId, padId);

  const handleChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const intValue = parseInt(event.target.value);
    setValue(isNaN(intValue) ? 0 : intValue);
  };

  return (
    <input
      type="number"
      step="1"
      value={value || ""}
      onChange={handleChange}
      placeholder="Enter number..."
      className="input input-bordered w-full bg-base-300 border-2 border-black border-b-4 border-r-4 rounded-lg text-base-content placeholder-base-content/40 focus:border-primary focus:ring-2 focus:ring-primary font-vt323 text-sm hover:bg-base-100 transition-colors duration-150"
    />
  );
}
