/**
 * Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
 * SPDX-License-Identifier: SUL-1.0
 */

import {
  ContextMessageRole,
  ContextMessageRoleEnum,
} from "@gabber/client-react";
import { usePropertyPad } from "../hooks/usePropertyPad";
import { PropertyEditProps } from "./PropertyEdit";

export function ContextMessageRoleEdit({ nodeId, padId }: PropertyEditProps) {
  const { runtimeValue, setEditorValue: setValue } =
    usePropertyPad<ContextMessageRole>(nodeId, padId);

  const roleOptions = [
    { value: "system", label: "System" },
    { value: "user", label: "User" },
    { value: "assistant", label: "Assistant" },
  ];

  const handleChange = (event: React.ChangeEvent<HTMLSelectElement>) => {
    setValue({
      type: "context_message_role",
      value: event.target.value as ContextMessageRoleEnum,
    });
  };

  return (
    <select
      value={runtimeValue?.value || ""}
      onChange={handleChange}
      className="select select-bordered select-sm w-full bg-base-300 border-2 border-black border-b-4 border-r-4 rounded-lg text-base-content font-vt323 text-xs hover:bg-base-100 transition-colors duration-150 focus:outline-none"
    >
      <option value="" disabled className="text-base-content/60">
        Select a role
      </option>
      {roleOptions.map((option) => (
        <option
          key={option.value}
          value={option.value}
          className="text-base-content"
        >
          {option.label}
        </option>
      ))}
    </select>
  );
}
