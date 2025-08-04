/**
 * Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
 * SPDX-License-Identifier: SUL-1.0
 */

import { usePropertyPad } from "../hooks/usePropertyPad";
import { PropertyEditProps } from "./PropertyEdit";
import { useMemo } from "react";

export function EnumPropertyEdit({ nodeId, padId }: PropertyEditProps) {
  const { editorValue: value, setEditorValue: setValue, singleAllowedType } = usePropertyPad<string>(
    nodeId,
    padId,
  );

  const handleChange = (event: React.ChangeEvent<HTMLSelectElement>) => {
    setValue(event.target.value);
  };

  const options: string[] = useMemo(() => {
    if (!singleAllowedType || !singleAllowedType.options) {
      return [];
    }
    return singleAllowedType.options;
  }, [singleAllowedType]);

  return (
    <select
      value={value || ""}
      onChange={handleChange}
      className="select select-bordered w-full bg-base-300 border-2 border-black border-b-4 border-r-4 rounded-lg text-base-content placeholder-base-content/40 focus:border-primary focus:ring-2 focus:ring-primary font-vt323 text-sm hover:bg-base-100 transition-colors duration-150"
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
