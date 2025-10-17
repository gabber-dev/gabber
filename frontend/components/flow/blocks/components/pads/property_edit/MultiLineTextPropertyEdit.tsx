/**
 * Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
 * SPDX-License-Identifier: SUL-1.0
 */

import { String } from "@gabber/client-react";
import { usePropertyPad } from "../hooks/usePropertyPad";
import { PropertyEditProps } from "./PropertyEdit";
import { useState, useEffect, useRef } from "react";

export function MultiLineTextPropertyEdit({
  nodeId,
  padId,
}: PropertyEditProps) {
  const { runtimeValue, setEditorValue: setValue } = usePropertyPad<String>(
    nodeId,
    padId,
  );
  const textareaRef = useRef<HTMLTextAreaElement | null>(null);

  const [localValue, setLocalValue] = useState(runtimeValue?.value || "");

  useEffect(() => {
    setLocalValue(runtimeValue?.value || "");
  }, [runtimeValue]);

  const autoResize = () => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = `${el.scrollHeight}px`;
  };

  useEffect(() => {
    autoResize();
  }, [localValue]);

  const handleChange = (event: React.ChangeEvent<HTMLTextAreaElement>) => {
    setLocalValue(event.target.value);
  };

  const handleBlur = () => {
    setValue({ type: "string", value: localValue });
  };

  return (
    <textarea
      ref={textareaRef}
      value={localValue}
      onChange={(e) => {
        handleChange(e);
        autoResize();
      }}
      onBlur={handleBlur}
      placeholder="Add your comment here..."
      rows={1}
      className="textarea textarea-bordered w-full bg-base-300 border-2 border-black border-b-4 border-r-4 rounded-lg text-base-content placeholder-base-content/40 focus:border-primary focus:ring-2 focus:ring-primary font-sans text-base leading-relaxed hover:bg-base-100 transition-colors duration-150 resize-none min-h-[72px]"
      style={{ overflow: "hidden" }}
    />
  );
}
