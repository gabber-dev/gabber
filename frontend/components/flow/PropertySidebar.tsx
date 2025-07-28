/**
 * Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
 * SPDX-License-Identifier: SUL-1.0
 */

import { useEditor } from "@/hooks/useEditor";
import { useState, useMemo, useEffect } from "react";
import { PropertyEdit } from "./blocks/components/pads/property_edit/PropertyEdit";
import { getDataTypeColor } from "./blocks/components/pads/utils/dataTypeColors";
import {
  PencilIcon,
  ClipboardDocumentIcon,
  TrashIcon,
} from "@heroicons/react/24/outline";

interface CollapsibleSectionProps {
  title: string;
  isOpen: boolean;
  onToggle: () => void;
  children: React.ReactNode;
}

function CollapsibleSection({
  title,
  isOpen,
  onToggle,
  children,
}: CollapsibleSectionProps) {
  return (
    <div className="border border-base-300 rounded-lg">
      <button
        className="w-full flex items-center justify-between p-3 hover:bg-base-50 transition-colors"
        onClick={onToggle}
      >
        <h3 className="text-md font-medium text-base-content/80">{title}</h3>
        <svg
          className={`w-4 h-4 transition-transform ${isOpen ? "rotate-180" : ""}`}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M19 9l-7 7-7-7"
          />
        </svg>
      </button>
      {isOpen && (
        <div className="p-3 space-y-4 border-t border-base-300">{children}</div>
      )}
    </div>
  );
}

interface PropertySidebarProps {
  onToggle: () => void;
}

export function PropertySidebar({ onToggle }: PropertySidebarProps) {
  const { reactFlowRepresentation, updateNode, removeNode } = useEditor();
  const [inputPadsOpen, setInputPadsOpen] = useState(true);
  const [outputPadsOpen, setOutputPadsOpen] = useState(true);

  // Node ID editing state
  const [localNodeId, setLocalNodeId] = useState<string>("");
  const [isEditingNodeId, setIsEditingNodeId] = useState(false);
  const [nodeIdError, setNodeIdError] = useState<string>("");
  const [copySuccess, setCopySuccess] = useState(false);

  const nodeIdPattern = /^[a-z0-9_]*$/;

  const isPadEditable = useMemo(() => {
    return (pad: any) => {
      const isPropertyPad = pad.type === "PropertySinkPad";
      const hasAllowedTypes =
        pad.allowed_types && pad.allowed_types.length === 1;

      return isPropertyPad && hasAllowedTypes;
    };
  }, []);

  const selectedNode = reactFlowRepresentation.nodes.find(
    (node: any) => node.selected,
  );

  // Sync local node ID with selected node
  useEffect(() => {
    if (selectedNode && !isEditingNodeId) {
      setLocalNodeId(selectedNode.data.id);
      setNodeIdError("");
    }
  }, [selectedNode?.data.id, isEditingNodeId, selectedNode]);

  const validateNodeId = (id: string): string => {
    if (!id.trim()) {
      return "Node ID cannot be empty";
    }
    if (!nodeIdPattern.test(id)) {
      return "Node ID can only contain lowercase letters, numbers, and underscores";
    }
    if (id !== selectedNode?.data.id) {
      const existingNode = reactFlowRepresentation.nodes.find(
        (node: any) =>
          node.data.id === id && node.data.id !== selectedNode?.data.id,
      );
      if (existingNode) {
        return "Node ID already exists";
      }
    }
    return "";
  };

  const handleNodeIdChange = (value: string) => {
    const filteredValue = value.replace(/[^a-z0-9_]/g, "");
    setLocalNodeId(filteredValue);

    if (nodeIdError) {
      setNodeIdError("");
    }
  };

  const handleNodeIdSubmit = (newId: string) => {
    const trimmedId = newId.trim();
    const error = validateNodeId(trimmedId);

    if (error) {
      setNodeIdError(error);
      return;
    }

    if (trimmedId !== selectedNode?.data.id) {
      updateNode({
        type: "update_node",
        id: selectedNode.data.id,
        editor_name: null,
        new_id: trimmedId,
        editor_position: null,
        editor_dimensions: null,
      });
    }
    setNodeIdError("");
    setIsEditingNodeId(false);
  };

  const handleNodeIdKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter") {
      e.currentTarget.blur();
    } else if (e.key === "Escape") {
      setLocalNodeId(selectedNode?.data.id || "");
      setNodeIdError("");
      e.currentTarget.blur();
    }
  };

  const handleCopyNodeId = async () => {
    try {
      await navigator.clipboard.writeText(selectedNode?.data.id || "");
      setCopySuccess(true);
      setTimeout(() => setCopySuccess(false), 2000); // Reset after 2 seconds
    } catch (err) {
      console.error("Failed to copy node ID:", err);
    }
  };

  const handleDeleteNode = () => {
    if (selectedNode && confirm("Are you sure you want to delete this node?")) {
      removeNode({
        type: "remove_node",
        node_id: selectedNode.data.id,
      });
    }
  };

  if (!selectedNode) {
    return null;
  }

  const inputPads =
    selectedNode.data.pads?.filter(
      (pad: any) =>
        pad.type === "StatelessSinkPad" || pad.type === "PropertySinkPad",
    ) || [];
  const outputPads =
    selectedNode.data.pads?.filter(
      (pad: any) =>
        pad.type === "StatelessSourcePad" || pad.type === "PropertySourcePad",
    ) || [];

  const renderPadConnections = (pad: any) => {
    const hasConnections =
      (pad.next_pads && pad.next_pads.length > 0) || pad.previous_pad;

    return (
      <div className="flex items-center gap-2 text-xs">
        <div
          className={`w-2 h-2 rounded-full ${hasConnections ? "bg-success" : "bg-base-400"}`}
        />
        <span
          className={hasConnections ? "text-success" : "text-base-content/40"}
        >
          {hasConnections ? "Connected" : "Disconnected"}
        </span>
      </div>
    );
  };

  const renderPad = (pad: any) => (
    <div key={pad.id} className="bg-base-200 p-3 rounded-lg">
      <div className="mb-2">
        <span className="font-medium text-sm block">{pad.id}</span>
        {renderPadConnections(pad)}
      </div>

      {isPadEditable(pad) ? (
        <div className="mt-3">
          <span className="font-medium text-xs text-base-content/70 block mb-2">
            Value:
          </span>
          <div className="relative">
            <PropertyEdit
              nodeId={selectedNode?.data.id || "not_set"}
              padId={pad.id}
            />
          </div>
        </div>
      ) : (
        pad.value !== undefined &&
        pad.value !== null && (
          <div className="text-xs text-base-content/60 mt-2">
            <span className="font-medium">Value:</span>
            <div className="font-mono bg-base-300 p-1 rounded mt-1 overflow-x-auto whitespace-nowrap max-w-full">
              {typeof pad.value === "string"
                ? pad.value
                : JSON.stringify(pad.value)}
            </div>
          </div>
        )
      )}

      {pad.allowed_types && pad.allowed_types.length > 0 && (
        <div className="text-xs text-base-content/60 mt-2">
          <span className="font-medium">Allowed types:</span>
          <div className="flex flex-wrap gap-1 mt-1">
            {pad.allowed_types.map((type: any, index: number) => {
              const typeName =
                typeof type === "string"
                  ? type
                  : type.type || JSON.stringify(type);
              const dataTypeColor = getDataTypeColor(typeName);

              return (
                <span
                  key={index}
                  className="px-1 py-0.5 rounded text-xs text-white font-medium"
                  style={{
                    background: dataTypeColor.background,
                    border: `1px solid ${dataTypeColor.border}`,
                  }}
                >
                  {typeName}
                </span>
              );
            })}
          </div>
        </div>
      )}

      {pad.next_pads && pad.next_pads.length > 0 && (
        <div className="text-xs text-base-content/60 mt-2">
          <span className="font-medium">→ Outputs to:</span>
          <div className="space-y-1 mt-1">
            {pad.next_pads.map((nextPad: any, index: number) => (
              <div
                key={index}
                className="font-mono text-xs bg-success/10 text-success p-1 rounded overflow-x-auto whitespace-nowrap"
              >
                {nextPad.node}:{nextPad.pad}
              </div>
            ))}
          </div>
        </div>
      )}

      {pad.previous_pad && (
        <div className="text-xs text-base-content/60 mt-2">
          <span className="font-medium">← Input from:</span>
          <div className="font-mono text-xs bg-info/10 text-info p-1 rounded mt-1 overflow-x-auto whitespace-nowrap">
            {pad.previous_pad.node}:{pad.previous_pad.pad}
          </div>
        </div>
      )}
    </div>
  );

  return (
    <div className="w-80 h-full flex flex-col bg-base-200">
      <div className="bg-base-200 p-4 border-b border-base-300 flex justify-between items-center">
        <div className="flex-1 group relative">
          <input
            type="text"
            value={selectedNode.data.editor_name}
            onChange={(e) => {
              updateNode({
                type: "update_node",
                id: selectedNode.data.id,
                editor_name: e.target.value,
                new_id: null,
                editor_position: null,
                editor_dimensions: null,
              });
            }}
            className="text-lg font-semibold bg-transparent border-none outline-none focus:bg-base-100 focus:px-2 focus:py-1 focus:rounded transition-colors w-full cursor-text"
            placeholder="Node display name"
          />
          <PencilIcon className="absolute right-2 top-1/2 -translate-y-1/2 h-4 w-4 text-base-content/30 opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none" />
        </div>
      </div>

      <div className="flex-1 p-4 space-y-4 overflow-y-auto">
        <div className="bg-base-200 p-3 rounded-lg">
          <label className="text-sm font-medium text-base-content/70 block mb-2">
            Node ID
          </label>
          <div className="flex gap-2">
            <input
              type="text"
              value={
                isEditingNodeId ? localNodeId : selectedNode?.data.id || ""
              }
              onFocus={() => {
                setIsEditingNodeId(true);
                setLocalNodeId(selectedNode?.data.id || "");
              }}
              onChange={(e) => {
                if (isEditingNodeId) {
                  handleNodeIdChange(e.target.value);
                }
              }}
              onBlur={() => {
                handleNodeIdSubmit(localNodeId);
              }}
              onKeyDown={handleNodeIdKeyDown}
              className="text-sm text-base-content font-mono bg-base-300 p-2 rounded flex-1 border-none outline-none focus:bg-base-100 transition-colors"
              placeholder="Node ID"
            />
            <button
              onClick={handleCopyNodeId}
              className={`btn btn-sm p-2 transition-all duration-200 ${
                copySuccess
                  ? "btn-success text-success-content"
                  : "btn-ghost text-base-content/60 hover:text-base-content"
              }`}
              title={copySuccess ? "Copied!" : "Copy Node ID"}
            >
              {copySuccess ? (
                <svg
                  className="h-4 w-4"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M5 13l4 4L19 7"
                  />
                </svg>
              ) : (
                <ClipboardDocumentIcon className="h-4 w-4" />
              )}
            </button>
          </div>
          {nodeIdError && (
            <div className="text-xs text-error mt-1">{nodeIdError}</div>
          )}
        </div>

        {inputPads.length > 0 && (
          <CollapsibleSection
            title={`Input Pads (${inputPads.length})`}
            isOpen={inputPadsOpen}
            onToggle={() => setInputPadsOpen(!inputPadsOpen)}
          >
            <div className="space-y-2">{inputPads.map(renderPad)}</div>
          </CollapsibleSection>
        )}

        {outputPads.length > 0 && (
          <CollapsibleSection
            title={`Output Pads (${outputPads.length})`}
            isOpen={outputPadsOpen}
            onToggle={() => setOutputPadsOpen(!outputPadsOpen)}
          >
            <div className="space-y-2">{outputPads.map(renderPad)}</div>
          </CollapsibleSection>
        )}

        {inputPads.length === 0 && outputPads.length === 0 && (
          <div className="text-center text-base-content/60 p-4">
            <div className="text-2xl mb-2">🔌</div>
            <div>No pads available</div>
          </div>
        )}
      </div>

      {/* Delete Node Button */}
      <div className="p-4 border-t border-base-300">
        <button
          onClick={handleDeleteNode}
          className="btn btn-error btn-sm w-full gap-2"
          title="Delete Node"
        >
          <TrashIcon className="h-4 w-4" />
          Delete Node
        </button>
      </div>
    </div>
  );
}
