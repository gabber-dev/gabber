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
}

const DEFAULT_TOOL_SCHEMA = {
  type: "object",
  properties: {
    input: {
      type: "string",
      description: "Input parameter",
    },
  },
  required: ["input"],
};

export function ToolGroupEditModal({
  tools: initialTools,
  onClose,
}: ToolGroupEditModalProps) {
  const [tools, setTools] = useState<ToolDefinition[]>(initialTools);
  const [selectedToolId, setSelectedToolId] = useState<string | null>(null);
  const [hasChanges, setHasChanges] = useState(false);
  const initialJSONRef = useRef<string>("");

  const selectedTool = tools.find((t) => t.id === selectedToolId);

  // Track changes
  // TODO
  useEffect(() => {}, []);

  const addTool = () => {
    // TODO
  };

  const updateTool = (toolId: string, updates: Partial<ToolDefinition>) => {
    setTools((prev) =>
      prev.map((t) => (t.id === toolId ? { ...t, ...updates } : t)),
    );
    setSelectedToolId(toolId);
  };

  const deleteTool = (toolId: string) => {
    setTools((prev) => prev.filter((t) => t.id !== toolId));
    setSelectedToolId(toolId);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black bg-opacity-50 backdrop-blur-sm"
        onClick={onClose}
      />

      {/* Modal */}
      <div className="relative w-full max-w-6xl max-h-[90vh] bg-base-100 rounded-xl shadow-2xl overflow-hidden">
        <div className="flex flex-col h-full">
          {/* Header */}
          <div className="flex items-center justify-between p-6 border-b border-base-300">
            <h2 className="text-2xl font-bold">Edit Tools</h2>
            <button onClick={onClose} className="btn btn-ghost btn-circle">
              <XMarkIcon className="w-6 h-6" />
            </button>
          </div>

          <div className="flex flex-1 overflow-hidden">
            {/* Left Panel - Tool List */}
            <div className="w-96 border-r border-base-300 flex flex-col">
              <div className="p-6 border-b border-base-300">
                <div className="flex items-center justify-between">
                  <h3 className="text-lg font-semibold">Tools</h3>
                  <button onClick={addTool} className="btn btn-sm btn-primary">
                    <PlusIcon className="w-4 h-4 mr-1" />
                    Add Tool
                  </button>
                </div>
              </div>

              <div className="flex-1 overflow-y-auto px-6 py-4 space-y-3">
                {tools.length === 0 ? (
                  <div className="text-center text-base-content/60 py-16">
                    <div className="bg-base-200 border-2 border-dashed rounded-xl w-20 h-20 mx-auto mb-4" />
                    <p>No tools yet. Add one to get started.</p>
                  </div>
                ) : (
                  tools.map((tool) => (
                    <div
                      key={tool.name}
                      className={`collapse collapse-arrow rounded-lg transition-all ${
                        selectedToolId === tool.id
                          ? "bg-primary/10 border border-primary/50"
                          : "bg-base-200"
                      }`}
                    >
                      <input
                        type="radio"
                        name="tool-accordion"
                        checked={selectedToolId === tool.name}
                        onChange={() => setSelectedToolId(tool.name)}
                      />
                      <div className="collapse-title text-sm font-medium pr-10 flex items-center justify-between">
                        <span className="truncate">
                          {tool.name || "Untitled Tool"}
                        </span>
                        <span
                          className={`badge badge-sm ml-2 ${
                            tool.destination === "webhook"
                              ? "badge-accent"
                              : "badge-primary"
                          }`}
                        >
                          {tool.destination}
                        </span>
                      </div>

                      <div className="collapse-content space-y-3 pt-3">
                        <input
                          type="text"
                          className="input input-sm w-full"
                          placeholder="Tool name"
                          value={tool.name}
                          onChange={(e) =>
                            updateTool(tool.name, { name: e.target.value })
                          }
                        />

                        <div className="flex gap-2">
                          <button
                            onClick={() => deleteTool(tool.name)}
                            className="btn btn-xs btn-ghost text-error"
                            title="Delete"
                          >
                            <TrashIcon className="w-4 h-4" />
                          </button>
                        </div>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>

            {/* Right Panel - Selected Tool Editor */}
            <div className="flex-1 flex flex-col">
              <div className="p-6 border-b border-base-300 space-y-4">
                {selectedTool ? (
                  <>
                    <h3 className="text-xl font-semibold">
                      {selectedTool.name || "Untitled Tool"}
                    </h3>

                    {/* Destination & Webhook URL */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div>
                        <label className="label">
                          <span className="label-text font-medium">
                            Destination
                          </span>
                        </label>
                        <select
                          className="select select-bordered w-full"
                          value={selectedTool.destination}
                          onChange={(e) =>
                            updateTool(selectedTool.name, {
                              destination: e.target.value as
                                | "client"
                                | "webhook",
                              webhookUrl:
                                e.target.value === "client"
                                  ? undefined
                                  : selectedTool.webhookUrl || "",
                            })
                          }
                        >
                          <option value="client">Client Tool</option>
                          <option value="webhook">Webhook</option>
                        </select>
                      </div>

                      {selectedTool.destination === "webhook" && (
                        <div>
                          <label className="label">
                            <span className="label-text font-medium">
                              Webhook URL
                            </span>
                          </label>
                          <div className="relative">
                            <LinkIcon className="absolute left-3 top-3 w-5 h-5 text-base-content/40" />
                            <input
                              type="url"
                              className="input input-bordered w-full pl-10"
                              placeholder="https://example.com/webhook"
                              value={selectedTool.webhookUrl || ""}
                              onChange={(e) =>
                                updateTool(selectedTool.id, {
                                  webhookUrl: e.target.value,
                                })
                              }
                            />
                          </div>
                        </div>
                      )}
                    </div>
                  </>
                ) : (
                  <div className="text-center py-12 text-base-content/50">
                    <div className="bg-base-200 border-2 border-dashed rounded-xl w-24 h-24 mx-auto mb-4" />
                    <p>Select a tool to edit its configuration and schema</p>
                  </div>
                )}
              </div>

              {/* JSON Schema Editor */}
              <div className="flex-1 p-6">
                {selectedTool ? (
                  <Editor
                    height="100%"
                    defaultLanguage="json"
                    value={JSON.stringify(selectedTool.bodySchema, null, 2)}
                    onChange={(value) => {
                      if (!value) return;
                      try {
                        const parsed = JSON.parse(value);
                        updateTool(selectedTool.name, { bodySchema: parsed });
                      } catch {
                        // Ignore invalid JSON during typing
                      }
                    }}
                    theme="vs-dark"
                    options={{
                      minimap: { enabled: false },
                      fontSize: 14,
                      wordWrap: "on",
                      formatOnPaste: true,
                      formatOnType: true,
                      scrollBeyondLastLine: false,
                      automaticLayout: true,
                    }}
                  />
                ) : (
                  <div className="h-full flex items-center justify-center text-base-content/40">
                    <p>No tool selected</p>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Footer */}
          <div className="flex justify-between items-center p-6 border-t border-base-300">
            <div>
              {hasChanges && (
                <span className="text-sm text-warning flex items-center gap-1">
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
                onClick={() => {}}
                disabled={!hasChanges}
                className="btn btn-primary"
              >
                Save Changes
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
