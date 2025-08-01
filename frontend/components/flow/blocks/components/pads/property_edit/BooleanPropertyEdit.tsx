/**
 * Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
 * SPDX-License-Identifier: SUL-1.0
 */

import { usePropertyPad } from "../hooks/usePropertyPad";
import { PropertyEditProps } from "./PropertyEdit";

export function BooleanPropertyEdit({ nodeId, padId }: PropertyEditProps) {
  const { value, setValue } = usePropertyPad<boolean>(nodeId, padId);

  const handleToggle = () => {
    setValue(!value);
  };

  return (
    <div className="flex items-center justify-between bg-base-300 border-2 border-black border-b-4 border-r-4 rounded-lg py-1.5 px-3 hover:bg-base-100 transition-colors duration-150">
      <span className="font-vt323 text-xs text-base-content">
        {value ? "TRUE" : "FALSE"}
      </span>
      <input
        type="checkbox"
        checked={value || false}
        onChange={handleToggle}
        className="toggle toggle-primary toggle-sm bg-base-300 border-2 border-black border-b-4 border-r-4 rounded-lg focus:outline-none"
      />
    </div>
  );
}
