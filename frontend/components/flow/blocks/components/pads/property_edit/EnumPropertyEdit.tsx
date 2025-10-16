/**
 * Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
 * SPDX-License-Identifier: SUL-1.0
 */

import { Enum } from "@gabber/client-react";
import { usePropertyPad } from "../hooks/usePropertyPad";
import { PropertyEditProps } from "./PropertyEdit";
import { useMemo } from "react";

export function EnumPropertyEdit({ nodeId, padId }: PropertyEditProps) {
  const {
    runtimeValue,
    setEditorValue: setValue,
    singleAllowedType,
  } = usePropertyPad<Enum>(nodeId, padId);

  const handleChange = (event: React.ChangeEvent<HTMLSelectElement>) => {
    setValue(event.target.value);
  };

  const options: string[] = useMemo(() => {
    if (!singleAllowedType || !singleAllowedType.options) {
      return [];
    }
    return singleAllowedType.options as string[];
  }, [singleAllowedType]);

  return (
    <select
      value={runtimeValue || ""}
      onChange={handleChange}
      className="select select-bordered select-xs p-0 w-full bg-base-300 border-2 border-black border-b-4 border-r-4 rounded-lg text-base-content placeholder-base-content/40 focus:border-primary focus:ring-2 focus:ring-primary font-vt323 hover:bg-base-100 transition-colors duration-150"
    >
      <option value="">Select</option>
      {options.map((enumOption) => (
        <option key={enumOption} value={enumOption}>
          {enumOption}
        </option>
      ))}
    </select>
  );
}
