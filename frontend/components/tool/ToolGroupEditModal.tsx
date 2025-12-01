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
import {
  Object,
  ToolDefinition,
  ToolDefinitionDestination_Webhook_RetryPolicy,
} from "@/generated/editor";
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

  const selectedTool = tools.find((_, i) => i === selectedIdx);

  const addTool = () => {
    const newTool = {
      ...DEFAULT_TOOL,
      id: crypto.randomUUID(),
      name: `new_tool_${tools.length + 1}`,
    };
    setTools((prev) => [...prev, newTool]);
    setSelectedIdx(tools.length);
    setHasChanges(true);
  };

  const updateTool = (name: string, updates: Partial<ToolDefinition>) => {
    setTools((prev) =>
      prev.map((t) => (t.name === name ? { ...t, ...updates } : t)),
    );
    setHasChanges(true);
  };

  const deleteTool = (idx: number) => {
    setTools((prev) => prev.filter((_, i) => i !== idx));
    setHasChanges(true);

    if (selectedIdx === idx) {
      const newIdx = idx > 0 ? idx - 1 : tools.length > 1 ? 0 : -1;
      setSelectedIdx(newIdx);
    } else if (selectedIdx > idx) {
      setSelectedIdx(selectedIdx - 1);
    }
  };

  const handleSave = () => {
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

      {/* Main Content */}
      <div className="flex flex-1 overflow-hidden">
        {/* Tools List Sidebar */}
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

        {/* Tool Editor */}
        <div className="flex-1 flex flex-col">
          {selectedTool ? (
            <>
              {/* Tool Metadata */}
              <div className="p-4 border-b border-base-300 space-y-4">
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

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
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

                          if (type === "client") {
                            updateTool(selectedTool.name, {
                              destination: { type: "client" },
                            });
                          } else {
                            // Preserve existing webhook config when switching back
                            const existing =
                              selectedTool.destination.type === "webhook"
                                ? selectedTool.destination
                                : {
                                    url: "",
                                    retry_policy: {
                                      max_retries: 3,
                                      initial_delay_seconds: 1,
                                      backoff_factor: 2,
                                    } as ToolDefinitionDestination_Webhook_RetryPolicy,
                                  };

                            updateTool(selectedTool.name, {
                              destination: {
                                type: "webhook",
                                url: existing.url || "",
                                retry_policy: existing.retry_policy,
                              },
                            });
                          }
                        }}
                      >
                        <option value="client">Client Tool</option>
                        <option value="webhook">Webhook</option>
                      </select>
                    </div>

                    {selectedTool.destination.type === "webhook" && (
                      <>
                        <div>
                          <label className="label label-text text-xs font-medium">
                            Webhook URL
                          </label>
                          <div className="relative">
                            <LinkIcon className="absolute left-3 top-2.5 w-4 h-4 text-base-content/40 pointer-events-none" />
                            <input
                              type="url"
                              className="input input-bordered input-sm w-full pl-10"
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

                        {/* Retry Policy */}
                        <div className="col-span-2 border-t border-base-300 pt-4 -mx-4 px-4 bg-base-100">
                          <h4 className="text-xs font-semibold mb-3">
                            Retry Policy
                          </h4>
                          <div className="grid grid-cols-3 gap-3">
                            <div>
                              <label className="label label-text text-xs">
                                Max Retries
                              </label>
                              <input
                                type="number"
                                min="0"
                                max="20"
                                className="input input-bordered input-xs w-full"
                                value={
                                  selectedTool.destination.type === "webhook"
                                    ? (selectedTool.destination.retry_policy
                                        ?.max_retries ?? 3)
                                    : 0
                                }
                                onChange={(e) => {
                                  const newDest = {
                                    ...selectedTool.destination,
                                  };
                                  if (newDest.type !== "webhook") return;
                                  newDest.retry_policy = {
                                    ...(newDest.retry_policy ?? {
                                      initial_delay_seconds: 1,
                                      backoff_factor: 2,
                                    }),
                                    max_retries: parseInt(e.target.value) || 0,
                                  };
                                  updateTool(selectedTool.name, {
                                    destination: {
                                      ...selectedTool.destination,
                                    },
                                  });
                                }}
                              />
                            </div>
                            <div>
                              <label className="label label-text text-xs">
                                Initial Delay (s)
                              </label>
                              <input
                                type="number"
                                min="0.1"
                                step="0.1"
                                className="input input-bordered input-xs w-full"
                                value={
                                  selectedTool.destination.retry_policy
                                    ?.initial_delay_seconds ?? 1
                                }
                                onChange={(e) => {
                                  const newDest = {
                                    ...selectedTool.destination,
                                  };
                                  if (newDest.type !== "webhook") return;
                                  newDest.retry_policy = {
                                    ...(newDest.retry_policy ?? {
                                      max_retries: 3,
                                      backoff_factor: 2,
                                    }),
                                    initial_delay_seconds:
                                      parseFloat(e.target.value) || 1,
                                  };
                                  updateTool(selectedTool.name, {
                                    destination: {
                                      ...selectedTool.destination,
                                    },
                                  });
                                }}
                              />
                            </div>
                            <div>
                              <label className="label label-text text-xs">
                                Backoff Factor
                              </label>
                              <input
                                type="number"
                                min="1"
                                step="0.5"
                                className="input input-bordered input-xs w-full"
                                value={
                                  selectedTool.destination.retry_policy
                                    ?.backoff_factor ?? 2
                                }
                                onChange={(e) => {
                                  const newDest = {
                                    ...selectedTool.destination,
                                  };
                                  if (newDest.type !== "webhook") return;
                                  newDest.retry_policy = {
                                    ...(newDest.retry_policy ?? {
                                      max_retries: 3,
                                      initial_delay_seconds: 1,
                                    }),
                                    backoff_factor:
                                      parseFloat(e.target.value) || 2,
                                  };
                                  updateTool(selectedTool.name, {
                                    destination: {
                                      ...selectedTool.destination,
                                    },
                                  });
                                }}
                              />
                            </div>
                          </div>
                        </div>
                      </>
                    )}
                  </div>
                </div>
              </div>

              {/* JSON Schema Editor */}
              <div className="flex flex-col flex-1 p-4">
                <div className="bg-base-200 px-3 py-1 border-b border-base-300 text-xs font-medium">
                  Parameters (JSON Schema)
                </div>
                <div className="relative border border-base-300 grow w-full">
                  <Editor
                    className="absolute inset-0"
                    defaultLanguage="json"
                    value={JSON.stringify(selectedTool.parameters, null, 2)}
                    onChange={(value) => {
                      if (!value) return;
                      try {
                        const parsed = JSON.parse(value);
                        updateTool(selectedTool.name, {
                          parameters: parsed,
                        });
                      } catch (e) {
                        // Invalid JSON — ignore
                      }
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
