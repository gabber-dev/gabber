/**
 * Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
 * SPDX-License-Identifier: SUL-1.0
 */

import { usePropertyPad } from "../hooks/usePropertyPad";
import { PropertyEditProps } from "./PropertyEdit";

export function MultiLineTextPropertyEdit({
  nodeId,
  padId,
}: PropertyEditProps) {
  const { runtimeValue, setEditorValue: setValue } = usePropertyPad<string>(
    nodeId,
    padId,
  );
  const handleChange = (event: React.ChangeEvent<HTMLTextAreaElement>) => {
    setValue(event.target.value);
  };

  return (
    <textarea
      value={runtimeValue || ""}
      onChange={handleChange}
      placeholder="Add your comment here..."
      rows={8}
      className="textarea textarea-bordered w-full bg-base-300 border-2 border-black border-b-4 border-r-4 rounded-lg text-base-content placeholder-base-content/40 focus:border-primary focus:ring-2 focus:ring-primary font-sans text-base leading-relaxed hover:bg-base-100 transition-colors duration-150 resize-none min-h-[160px] flex-1"
    />
  );
}
