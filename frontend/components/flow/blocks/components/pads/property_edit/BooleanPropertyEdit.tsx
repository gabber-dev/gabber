/**
 * Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
 * SPDX-License-Identifier: SUL-1.0
 */

import { Boolean } from "@gabber/client-react";
import { usePropertyPad } from "../hooks/usePropertyPad";
import { PropertyEditProps } from "./PropertyEdit";

export function BooleanPropertyEdit({ nodeId, padId }: PropertyEditProps) {
  const { runtimeValue, setEditorValue: setValue } = usePropertyPad<Boolean>(
    nodeId,
    padId,
  );

  const handleToggle = () => {
    setValue({ type: "boolean", value: !(runtimeValue?.value || false) });
  };

  return (
    <div className="flex items-center justify-between bg-base-300 border-2 border-black border-b-4 border-r-4 rounded-lg px-2 py-1 hover:bg-base-100 transition-colors duration-150">
      <span className="font-vt323 text-xs text-base-content">
        {runtimeValue?.value ? "TRUE" : "FALSE"}
      </span>
      <input
        type="checkbox"
        checked={runtimeValue?.value || false}
        onChange={handleToggle}
        className="toggle toggle-primary toggle-xs bg-base-300 border-2 border-black border-b-4 border-r-4 rounded-lg focus:outline-none"
      />
    </div>
  );
}
