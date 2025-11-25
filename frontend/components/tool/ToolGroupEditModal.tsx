"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import Editor from "@monaco-editor/react";
import {
  PlusIcon,
  TrashIcon,
  XMarkIcon,
  LinkIcon,
  BellAlertIcon,
} from "@heroicons/react/24/outline";
import { Object, ToolDefinition } from "@/generated/editor";
import { usePropertyPad } from "../flow/blocks/components/pads/hooks/usePropertyPad";

interface ToolGroupEditModalProps {
  node: string;
  pad: string;
  onClose: () => void;
}

const DEFAULT_TOOL: ToolDefinition = {
  name: "get_weather",
  description: "Get the current weather for a given location",
  destination: { type: "client" },
  parameters: {
    type: "object",
    properties: {
      location: {
        type: "string",
        description: "The city and state, e.g. San Francisco, CA",
      },
      unit: { type: "string", enum: ["celsius", "fahrenheit"] },
    },
    required: ["location"],
  },
};

export function ToolGroupEditModal({ node, onClose }: ToolGroupEditModalProps) {
  const { editorValue, setEditorValue } = usePropertyPad<Object>(
    node,
    "config",
  );

  const editorTools = useMemo(() => {
    if (!editorValue || !editorValue.value.tools) return [] as ToolDefinition[];
    return editorValue.value.tools as ToolDefinition[];
  }, [editorValue]);

  const [tools, setTools] = useState<ToolDefinition[]>(editorTools);
  const [selectedIdx, setSelectedIdx] = useState<number>(-1);
  const [hasChanges, setHasChanges] = useState(false);

  const selectedTool = tools.find((t, i) => i === selectedIdx);

  const addTool = () => {
    const newTool = {
      ...DEFAULT_TOOL,
      id: crypto.randomUUID(),
      name: `new_tool_${tools.length + 1}`,
    };
    setTools((prev) => [...prev, newTool]);
    setSelectedIdx(tools.length);
  };

  const updateTool = (name: string, updates: Partial<ToolDefinition>) => {
    setTools((prev) =>
      prev.map((t) => (t.name === name ? { ...t, ...updates } : t)),
    );
    setHasChanges(true);
  };

  const deleteTool = (idx: number) => {
    setTools((prev) => prev.filter((t, i) => i !== idx));
    if (selectedIdx === idx) {
      const remaining = tools.filter((t, i) => i !== idx);
      setSelectedIdx(idx > 0 ? idx - 1 : remaining.length > 0 ? 0 : -1);
    }
  };

  const handleSave = () => {
    console.log("Saving tools:", tools);
    setEditorValue({ type: "object", value: { tools } });
    setHasChanges(false);
    onClose();
  };

  return (
    <div className="w-full h-full bg-base-100 rounded-xl flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between p-3 border-b border-base-300">
        <h2 className="text-xl font-bold">Edit Tools</h2>
        <button onClick={onClose} className="btn btn-ghost btn-sm btn-circle">
          <XMarkIcon className="w-5 h-5" />
        </button>
      </div>

      <div className="flex flex-1 overflow-hidden">
        {/* Left: Tool List */}
        <div className="w-72 border-r border-base-300 flex flex-col">
          <div className="p-3 border-b border-base-300 flex justify-between items-center">
            <h3 className="font-medium text-sm">Tools ({tools.length})</h3>
            <button
              onClick={addTool}
              className="btn btn-square btn-primary btn-xs"
            >
              <PlusIcon className="w-4 h-4" />
            </button>
          </div>

          <div className="flex-1 overflow-y-auto">
            {tools.length === 0 ? (
              <div className="p-8 text-center text-base-content/40 text-sm">
                <div className="w-16 h-16 mx-auto mb-3 bg-base-200 border-2 border-dashed rounded-lg" />
                <p>No tools yet</p>
              </div>
            ) : (
              <div className="p-2 space-y-1">
                {tools.map((tool, idx) => (
                  <div
                    key={tool.name}
                    onClick={() => setSelectedIdx(idx)}
                    className={`p-2.5 rounded-md cursor-pointer border text-sm transition-all ${
                      selectedIdx === idx
                        ? "bg-primary/10 border-primary"
                        : "bg-base-200 border-transparent hover:bg-base-300"
                    }`}
                  >
                    <div className="flex items-center justify-between gap-2">
                      <div className="flex-1 min-w-0">
                        <p className="font-medium truncate">{tool.name}</p>
                        <p className="text-xs text-base-content/60 truncate">
                          {tool.description?.slice(0, 40)}...
                        </p>
                      </div>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          deleteTool(idx);
                        }}
                        className="btn btn-ghost btn-xs text-error"
                      >
                        <TrashIcon className="w-3.5 h-3.5" />
                      </button>
                    </div>
                    <div className="mt-1">
                      <span
                        className={`badge badge-xs ${
                          tool.destination.type === "webhook"
                            ? "badge-accent"
                            : "badge-primary"
                        }`}
                      >
                        {tool.destination.type}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Right: Editor */}
        <div className="flex-1 flex flex-col">
          {selectedTool ? (
            <>
              {/* Compact Metadata */}
              <div className="p-4 border-b border-base-300 space-y-3">
                {/* Tool Name */}
                <div>
                  <label className="label label-text text-xs font-medium">
                    Name
                  </label>
                  <input
                    type="text"
                    className="input input-bordered input-sm w-full"
                    value={selectedTool.name}
                    onChange={(e) =>
                      updateTool(selectedTool.name, { name: e.target.value })
                    }
                  />
                </div>

                {/* Description + Destination */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {/* Description */}
                  <div>
                    <label className="label label-text text-xs font-medium">
                      Description
                    </label>
                    <textarea
                      className="textarea textarea-bordered textarea-sm w-full h-20 resize-none"
                      value={selectedTool.description || ""}
                      onChange={(e) =>
                        updateTool(selectedTool.name, {
                          description: e.target.value,
                        })
                      }
                    />
                  </div>

                  {/* Destination */}
                  <div className="space-y-3">
                    <div>
                      <label className="label label-text text-xs font-medium">
                        Destination
                      </label>
                      <select
                        className="select select-bordered select-sm w-full"
                        value={selectedTool.destination.type}
                        onChange={(e) => {
                          const type = e.target.value as "client" | "webhook";
                          updateTool(selectedTool.name, {
                            destination:
                              type === "webhook"
                                ? {
                                    type: "webhook",
                                    url: selectedTool.destination.url ?? "",
                                  }
                                : { type: "client" },
                          });
                        }}
                      >
                        <option value="client">Client Tool</option>
                        <option value="webhook">Webhook</option>
                      </select>
                    </div>

                    {selectedTool.destination.type === "webhook" && (
                      <div>
                        <label className="label label-text text-xs font-medium">
                          Webhook URL
                        </label>
                        <div className="relative">
                          <LinkIcon className="absolute left-2.5 top-2.5 w-4 h-4 text-base-content/40 pointer-events-none" />
                          <input
                            type="url"
                            className="input input-bordered input-sm w-full"
                            placeholder="https://..."
                            value={selectedTool.destination.url ?? ""}
                            onChange={(e) =>
                              updateTool(selectedTool.name, {
                                destination: {
                                  ...selectedTool.destination,
                                  url: e.target.value,
                                },
                              })
                            }
                          />
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              </div>

              {/* Parameters Editor - Maximum height */}
              <div className="flex flex-col flex-1 p-4">
                <div className="bg-base-200 px-3 py-1 border-b border-base-300 text-xs font-medium">
                  Parameters (JSON Schema)
                </div>
                <div className="relative border border-base-300 grow w-full">
                  <Editor
                    className="absolute top-0 bottom-0 left-0 right-0"
                    defaultLanguage="json"
                    value={JSON.stringify(selectedTool.parameters, null, 2)}
                    onChange={(value) => {
                      if (!value) return;
                      try {
                        updateTool(selectedTool.name, {
                          parameters: JSON.parse(value),
                        });
                      } catch {}
                    }}
                    theme="vs-dark"
                    options={{
                      minimap: { enabled: false },
                      fontSize: 11,
                      wordWrap: "on",
                      automaticLayout: true,
                      scrollBeyondLastLine: false,
                      lineNumbers: "on",
                      folding: true,
                      glyphMargin: false,
                      lineDecorationsWidth: 0,
                      lineNumbersMinChars: 3,
                    }}
                  />
                </div>
              </div>
            </>
          ) : (
            <div className="flex-1 flex items-center justify-center text-base-content/40">
              <p className="text-sm">Select a tool to edit</p>
            </div>
          )}
        </div>
      </div>

      {/* Footer */}
      <div className="flex justify-between items-center p-3 border-t border-base-300">
        <div>
          {hasChanges && (
            <span className="text-warning text-xs flex items-center gap-1">
              <BellAlertIcon className="w-3.5 h-3.5" />
              Unsaved changes
            </span>
          )}
        </div>
        <div className="flex gap-2">
          <button onClick={onClose} className="btn btn-ghost btn-sm">
            Cancel
          </button>
          <button
            onClick={handleSave}
            disabled={!hasChanges}
            className="btn btn-primary btn-sm"
          >
            Save Changes
          </button>
        </div>
      </div>
    </div>
  );
}
