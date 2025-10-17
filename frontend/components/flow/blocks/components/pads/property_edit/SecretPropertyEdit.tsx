/**
 * Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
 * SPDX-License-Identifier: SUL-1.0
 */

import { Secret } from "@gabber/client-react";
import { usePropertyPad } from "../hooks/usePropertyPad";
import { PropertyEditProps } from "./PropertyEdit";
import { useMemo } from "react";

export function SecretPropertyEdit({ nodeId, padId }: PropertyEditProps) {
  const {
    setEditorValue: setValue,
    runtimeValue,
    singleAllowedType,
  } = usePropertyPad<Secret>(nodeId, padId);

  const handleChange = (event: React.ChangeEvent<HTMLSelectElement>) => {
    const name = options.find((o) => o.id === event.target.value)?.name || "";
    setValue({ type: "secret", secret_id: event.target.value, name });
  };

  const options: { name: string; id: string }[] = useMemo(() => {
    if (!singleAllowedType || !singleAllowedType.options) {
      return [];
    }
    const opts = singleAllowedType.options as { name: string; id: string }[];
    return opts;
  }, [singleAllowedType]);

  return (
    <select
      value={runtimeValue?.secret_id || ""}
      onChange={handleChange}
      className="select select-bordered select-sm w-full bg-base-300 border-2 border-black border-b-4 border-r-4 rounded-lg text-base-content placeholder-base-content/40 focus:border-primary focus:ring-2 focus:ring-primary font-vt323 text-xs hover:bg-base-100 transition-colors duration-150"
    >
      <option value="">Select secret...</option>
      {options.map((secret) => (
        <option key={secret.id} value={secret.id}>
          {secret.name}
        </option>
      ))}
    </select>
  );
}
