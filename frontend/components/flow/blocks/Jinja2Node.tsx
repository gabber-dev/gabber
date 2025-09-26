/**
 * Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
 * SPDX-License-Identifier: SUL-1.0
 */

import { useEditor } from "@/hooks/useEditor";
import { BaseBlockProps } from "./BaseBlock";
import { usePropertyPad } from "./components/pads/hooks/usePropertyPad";
import { CubeIcon } from "@heroicons/react/24/outline";
import { NodeName } from "./components/NodeName";
import { NodeId } from "./components/NodeId";
import { PropertyPad } from "./components/pads/PropertyPad";
import { useMemo, useState, useEffect, useRef } from "react";
import Editor from "@monaco-editor/react";
import { PadHandle } from "./components/pads/PadHandle";
import { PropertyEdit } from "./components/pads/property_edit/PropertyEdit";

function RenderedTab({ rendered }: { rendered: string }) {
  return (
    <div className="h-[200px] overflow-y-auto bg-base-300 p-2 whitespace-pre-wrap nodrag">
      {rendered}
    </div>
  );
}

export function Jinja2Node({ data }: BaseBlockProps) {
  const {} = useEditor();
  const { runtimeValue: jinjaRuntimeValue, setEditorValue } = usePropertyPad(
    data.id,
    "jinja_template",
  );
  const { pad: renderedOutputPad, runtimeValue: renderedOutputValue } =
    usePropertyPad(data.id, "rendered_output");
  const { pad: numPropertiesPad } = usePropertyPad(data.id, "num_properties");
  const propertyPads = useMemo(() => {
    const propertyNamePads = data.pads.filter((p) =>
      p.id.startsWith("property_name_"),
    );
    const propertyValuePads = data.pads.filter((p) =>
      p.id.startsWith("property_value_"),
    );
    const getNum = (id: string) => parseInt(id.split("_").pop() || "0", 10);
    const sortedNames = [...propertyNamePads].sort(
      (a, b) => getNum(a.id) - getNum(b.id),
    );
    const sortedValues = [...propertyValuePads].sort(
      (a, b) => getNum(a.id) - getNum(b.id),
    );
    if (sortedNames.length !== sortedValues.length) {
      console.warn("Mismatched property name and value pads");
      return [];
    }

    return sortedNames.map((namePad, index) => {
      const valuePad = sortedValues[index];
      return { namePad, valuePad };
    });
  }, [data]);

  const [activeTab, setActiveTab] = useState<"editor" | "rendered">("editor");

  const [localJinjaValue, setLocalJinjaValue] = useState(
    (jinjaRuntimeValue as string) || "",
  );

  useEffect(() => {
    setLocalJinjaValue((jinjaRuntimeValue as string) || "");
  }, [jinjaRuntimeValue]);

  const currentValueRef = useRef(localJinjaValue);

  useEffect(() => {
    currentValueRef.current = localJinjaValue;
  }, [localJinjaValue]);

  const editorRef = useRef<HTMLDivElement>(null);

  return (
    <div className="w-100 flex flex-col bg-base-200 border-2 border-black border-b-4 border-r-4 rounded-lg relative pb-2">
      <div className="flex w-full items-center gap-2 bg-base-300 border-b-2 border-black p-3 rounded-t-lg drag-handle cursor-grab active:cursor-grabbing">
        <CubeIcon className="h-5 w-5 text-accent" />
        <div className="flex-1">
          <NodeName />
          <NodeId />
        </div>
      </div>
      <div className="flex border-b border-black">
        <button
          className={`flex-1 px-4 py-2 ${activeTab === "editor" ? "bg-base-100 border-b-2 border-accent" : "bg-base-300"}`}
          onClick={() => setActiveTab("editor")}
        >
          Editor
        </button>
        <button
          className={`flex-1 px-4 py-2 ${activeTab === "rendered" ? "bg-base-100 border-b-2 border-accent" : "bg-base-300"}`}
          onClick={() => setActiveTab("rendered")}
        >
          Rendered
        </button>
      </div>
      <div className="relative p-2 w-full">
        {activeTab === "editor" ? (
          <Editor
            ref={editorRef}
            height="200px" // Adjust height as needed
            defaultLanguage="jinja" // Using 'jinja' for Jinja2 templates
            value={localJinjaValue}
            onChange={(value) => setLocalJinjaValue(value || "")}
            onMount={(editor) => {
              const handleBlur = () => {
                setEditorValue(currentValueRef.current);
              };
              const disposable = editor.onDidBlurEditorWidget(handleBlur);
              return () => disposable.dispose();
            }}
            className="nodrag focus:outline-none"
            theme="vs-dark" // Enable dark mode theme
            options={{
              minimap: { enabled: false },
              scrollBeyondLastLine: false,
              fontSize: 14,
              wordWrap: "on",
              automaticLayout: true,
              tabSize: 2,
              suggestOnTriggerCharacters: true,
              acceptSuggestionOnEnter: "on",
              acceptSuggestionOnCommitCharacter: true,
              lineNumbers: "off",
              glyphMargin: false,
              folding: false,
              lineDecorationsWidth: 0,
              lineNumbersMinChars: 0,
              insertSpaces: false,
            }}
          />
        ) : (
          <RenderedTab rendered={renderedOutputValue as string} />
        )}
      </div>
      <div className="flex flex-col">
        {renderedOutputPad && (
          <div className="flex justify-end">
            <div className="text-xs w-24 mr-2">rendered_output</div>
            <PadHandle data={renderedOutputPad} notes={[]} />
          </div>
        )}
        {numPropertiesPad && (
          <div className="w-full relative px-4 py-2">
            <PropertyPad nodeId={data.id} data={numPropertiesPad} notes={[]} />
          </div>
        )}

        {propertyPads.map(({ namePad, valuePad }, index) => (
          <div
            key={index}
            className="w-full relative flex space-x-2 flex-col border-t border-base-300 py-2"
          >
            <div className="flex gap-3 items-center">
              <div className="text-xs w-24 ml-2">Template Name</div>
              <div className="grow">
                <PropertyEdit nodeId={data.id} padId={namePad.id} />
              </div>
            </div>
            <div className="flex gap-1 items-center">
              <PadHandle data={valuePad} notes={[]} />
              <div className="text-xs ml-2 text-accent">value</div>
              <div className="text-neutral-200 text-xs italic">
                {(valuePad.value as string) || ""}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
