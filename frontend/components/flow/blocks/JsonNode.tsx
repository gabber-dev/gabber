/**
 * Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
 * SPDX-License-Identifier: SUL-1.0
 */

import { useEditor } from "@/hooks/useEditor";
import { BaseBlockProps } from "./BaseBlock";
import { usePropertyPad } from "./components/pads/hooks/usePropertyPad";
import { JsonEditor, githubDarkTheme } from "json-edit-react";
import { PadHandle } from "./components/pads/PadHandle";
import { usePad } from "@gabber/client-react";
import { CubeIcon } from "@heroicons/react/24/outline";
import { useCallback } from "react";
import { useStatelessPad } from "./components/pads/hooks/useStatelessPad";

export function JsonNode({ data }: BaseBlockProps) {
  const {} = useEditor();
  const { runtimeValue, setEditorValue, pad } = usePropertyPad(
    data.id,
    "value",
  );
  const { pad: emitData } = useStatelessPad("emit");

  const handleIdClick = useCallback(async () => {
    try {
      await navigator.clipboard.writeText(data.id);
    } catch (err) {
      console.error("Failed to copy ID:", err);
    }
  }, [data.id]);

  return (
    <div className="w-100 flex flex-col bg-base-200 border-2 border-black border-b-4 border-r-4 rounded-lg relative pb-2">
      <div className="flex w-full items-center gap-2 bg-base-300 border-b-2 border-black p-3 rounded-t-lg drag-handle cursor-grab active:cursor-grabbing">
        <CubeIcon className="h-5 w-5 text-accent" />
        <div className="flex-1">
          <h2 className="text-lg text-primary font-medium">
            {data.editor_name}
          </h2>
          <div
            className="text-xs text-base-content/60 font-mono cursor-pointer hover:text-primary transition-colors select-none"
            onClick={handleIdClick}
            title="Click to copy ID"
          >
            {data.id}
          </div>
        </div>
      </div>
      <div className="relative p-2 w-full">
        <JsonEditor
          theme={githubDarkTheme}
          data={runtimeValue || null}
          setData={setEditorValue}
        />
      </div>
      <div className="flex flex-col">
        <div className="relative w-full flex items-center justify-end">
          <div className="mr-4 text-accent">value</div>
          <div className="">{pad && <PadHandle data={pad} />}</div>
        </div>
        <div className="relative w-full flex items-center">
          <div className="">{emitData && <PadHandle data={emitData} />}</div>
          <div className="text-accent ml-4">emit</div>
        </div>
      </div>
    </div>
  );
}
