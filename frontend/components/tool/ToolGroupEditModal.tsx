"use client";

import { useEffect, useRef, useState } from "react";
import Editor from "@monaco-editor/react";
import {
  PlusIcon,
  TrashIcon,
  XMarkIcon,
  LinkIcon,
  BellAlertIcon,
} from "@heroicons/react/24/outline";
import { ToolDefinition } from "@/generated/editor";

interface ToolGroupEditModalProps {
  tools: ToolDefinition[];
  onClose: () => void;
  onSave?: (tools: ToolDefinition[]) => void;
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
      unit: {
        type: "string",
        enum: ["celsius", "fahrenheit"],
      },
    },
    required: ["location"],
  },
};

export function ToolGroupEditModal({
  tools: initialTools,
  onClose,
  onSave,
}: ToolGroupEditModalProps) {
  const [tools, setTools] = useState<ToolDefinition[]>(
    initialTools.map((t) => ({ ...t, id: t.id ?? crypto.randomUUID() })),
  );
  const [selectedName, setSelectedName] = useState<string | null>(
    tools[0]?.name ?? null,
  );
  const [hasChanges, setHasChanges] = useState(false);
  const initialDataRef = useRef<string>("");

  const selectedTool = tools.find((t) => t.name === selectedName);

  // Track changes
  useEffect(() => {
    const initial = JSON.stringify(initialTools);
    initialDataRef.current = initial;
    const current = JSON.stringify(tools);
    setHasChanges(current !== initial);
  }, [tools, initialTools]);

  const addTool = () => {
    const newTool = {
      ...DEFAULT_TOOL,
      id: crypto.randomUUID(),
      name: `new_tool_${tools.length + 1}`,
    };
    setTools((prev) => [...prev, newTool]);
    setSelectedName(newTool.id);
  };

  const updateTool = (id: string, updates: Partial<ToolDefinition>) => {
    setTools((prev) =>
      prev.map((t) => (t.id === id ? { ...t, ...updates } : t)),
    );
  };

  const deleteTool = (name: string) => {
    setTools((prev) => prev.filter((t) => t.name !== name));
    if (selectedName === name) {
      setSelectedName(tools.find((t) => t.name !== name)?.name ?? null);
    }
  };

  const handleSave = () => {
    onSave?.(tools);
    onClose();
  };

  return (
    <div className="w-full h-full bg-base-100 rounded-xl flex flex-col">
      <div className="flex items-center justify-between p-4 border-b border-base-300">
        <h2 className="text-2xl font-bold">Edit Tools</h2>
        <button onClick={onClose} className="btn btn-ghost btn-circle">
          <XMarkIcon className="w-6 h-6" />
        </button>
      </div>

      <div className="flex flex-1 overflow-hidden">
        <div className="w-80 border-r border-base-300 flex flex-col">
          <div className="p-4 border-b border-base-300 flex justify-between items-center">
            <h3 className="font-semibold">Tools ({tools.length})</h3>
            <button onClick={addTool} className="btn btn-sm btn-primary">
              <PlusIcon className="w-4 h-4" />
            </button>
          </div>

          <div className="flex-1 overflow-y-auto">
            {tools.length === 0 ? (
              <div className="p-12 text-center text-base-content/50">
                <div className="w-20 h-20 mx-auto mb-4 bg-base-200 border-2 border-dashed rounded-xl" />
                <p>No tools yet</p>
              </div>
            ) : (
              <div className="p-3 space-y-2">
                {tools.map((tool) => (
                  <div
                    key={tool.name}
                    onClick={() => setSelectedName(tool.name)}
                    className={`p-4 rounded-lg cursor-pointer transition-all border ${
                      selectedName === tool.id
                        ? "bg-primary/10 border-primary shadow-sm"
                        : "bg-base-200 border-transparent hover:bg-base-300"
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex-1 min-w-0">
                        <p className="font-medium truncate">
                          {tool.name || "Untitled"}
                        </p>
                        <p className="text-xs text-base-content/60 mt-1">
                          {tool.description?.slice(0, 50)}...
                        </p>
                      </div>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          deleteTool(tool.name!);
                        }}
                        className="btn btn-ghost btn-xs text-error ml-3"
                      >
                        <TrashIcon className="w-4 h-4" />
                      </button>
                    </div>
                    <div className="mt-2">
                      <span
                        className={`badge badge-sm ${
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
              <div className="p-6 border-b border-base-300 space-y-6">
                <div>
                  <label className="label">
                    <span className="label-text font-medium">Tool Name</span>
                  </label>
                  <input
                    type="text"
                    className="input input-bordered w-full"
                    value={selectedTool.name}
                    onChange={(e) =>
                      updateTool(selectedTool.name!, { name: e.target.value })
                    }
                  />
                </div>

                <div>
                  <label className="label">
                    <span className="label-text font-medium">Description</span>
                  </label>
                  <textarea
                    className="textarea textarea-bordered w-full h-24"
                    value={selectedTool.description}
                    onChange={(e) =>
                      updateTool(selectedTool.name!, {
                        description: e.target.value,
                      })
                    }
                  />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="label">
                      <span className="label-text font-medium">
                        Destination
                      </span>
                    </label>
                    <select
                      className="select select-bordered w-full"
                      value={selectedTool.destination.type}
                      onChange={(e) => {}}
                    >
                      <option value="client">Client Tool</option>
                      <option value="webhook">Webhook</option>
                    </select>
                  </div>

                  {selectedTool.destination.type === "webhook" && (
                    <div>
                      <label className="label">
                        <span className="label-text font-medium">
                          Webhook URL
                        </span>
                      </label>
                      <div className="relative">
                        <LinkIcon className="absolute left-3 top-3.5 w-5 h-5 text-base-content/40" />
                        <input
                          type="url"
                          className="input input-bordered w-full pl-10"
                          placeholder="https://example.com/api/tool"
                          value={selectedTool.destination.url ?? ""}
                          onChange={(e) =>
                            updateTool(selectedTool.name!, {
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

              <div className="flex-1 p-6">
                <div className="h-full border border-base-300 rounded-lg overflow-hidden">
                  <Editor
                    height="100%"
                    defaultLanguage="json"
                    value={JSON.stringify(selectedTool.parameters, null, 2)}
                    onChange={(value) => {
                      if (!value) return;
                      try {
                        const parsed = JSON.parse(value);
                        updateTool(selectedTool.name!, {
                          parameters: parsed,
                        });
                      } catch {
                        // Invalid JSON - ignore
                      }
                    }}
                    theme="vs-dark"
                    options={{
                      minimap: { enabled: false },
                      fontSize: 14,
                      wordWrap: "on",
                      automaticLayout: true,
                      scrollBeyondLastLine: false,
                    }}
                  />
                </div>
              </div>
            </>
          ) : (
            <div className="flex-1 flex items-center justify-center text-base-content/40">
              <p>Select a tool to edit</p>
            </div>
          )}
        </div>
      </div>

      {/* Footer */}
      <div className="flex justify-between items-center p-6 border-t border-base-300">
        <div>
          {hasChanges && (
            <span className="text-warning text-sm flex items-center gap-1">
              <BellAlertIcon className="w-4 h-4" />
              Unsaved changes
            </span>
          )}
        </div>
        <div className="flex gap-3">
          <button onClick={onClose} className="btn btn-ghost">
            Cancel
          </button>
          <button
            onClick={handleSave}
            disabled={!hasChanges}
            className="btn btn-primary"
          >
            Save Changes
          </button>
        </div>
      </div>
    </div>
  );
}
