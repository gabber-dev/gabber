/**
 * Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
 * SPDX-License-Identifier: SUL-1.0
 */

import { PlayIcon, StopIcon } from "@heroicons/react/24/solid";
import { useCallback, useMemo } from "react";
import { useRun } from "@/hooks/useRun";
import { useEditor } from "@/hooks/useEditor";
import toast from "react-hot-toast";

// Validation function to check for empty dropdowns only
const validateGraphForEmptyDropdowns = (graph: any): string[] => {
  const issues: string[] = [];

  if (!graph.nodes) return issues;

  for (const node of graph.nodes) {
    if (node.pads) {
      for (const pad of node.pads) {
        // Check for empty string values in dropdown-like parameters
        if (pad.value === "" && pad.allowed_types?.includes("string") && (
          pad.id.toLowerCase().includes("secret") ||
          pad.id.toLowerCase().includes("key") ||
          pad.id.toLowerCase().includes("token") ||
          pad.id.toLowerCase().includes("api") ||
          pad.id.toLowerCase().includes("model")
        )) {
          issues.push(`${node.editor_name || node.id} has unselected dropdown: ${pad.id}`);
        }
      }
    }
  }

  return issues;
};

export function DebugControls() {
  const { connectionState, startRun, stopRun } = useRun();
  const { editorRepresentation } = useEditor();

  const buttonIcon = useMemo(() => {
    if (connectionState === "disconnected") {
      return <PlayIcon className="w-8 h-8" />;
    } else if (connectionState === "connecting") {
      return <div className="loading loading-dots loading-lg" />;
    } else if (connectionState === "connected") {
      return <StopIcon className="w-8 h-8" />;
    }
    return null;
  }, [connectionState]);

  const buttonAction = useCallback(() => {
    if (connectionState === "disconnected") {
      // Validate for empty dropdowns before running
      const validationIssues = validateGraphForEmptyDropdowns(editorRepresentation);
      if (validationIssues.length > 0) {
        toast.error("Please select all dropdown options before running:\n" + validationIssues.join("\n"));
        return;
      }
      startRun({ graph: editorRepresentation });
    } else if (connectionState === "connecting") {
      stopRun();
    } else if (connectionState === "connected") {
      stopRun();
    }
  }, [connectionState, editorRepresentation, startRun, stopRun]);

  const getButtonText = () => {
    if (connectionState === "disconnected") {
      return "Run";
    } else if (connectionState === "connecting") {
      return "Starting...";
    } else if (connectionState === "connected") {
      return "Stop";
    }
    return "";
  };

  return (
    <div className="flex items-center">
      <button
        onClick={() => {
          buttonAction();
        }}
        className={`
          btn btn-lg gap-3 font-medium transition-all duration-200
          ${
            connectionState === "disconnected"
              ? "btn-primary border border-neutral/30 hover:border-neutral/50"
              : connectionState === "connecting"
                ? "btn-primary border border-neutral/30"
                : "btn-secondary border border-neutral/30 hover:border-neutral/50"
          }
          min-w-[120px] h-9 px-4 rounded-md
        `}
      >
        {buttonIcon}
        <span className="text-base font-bold">{getButtonText()}</span>
      </button>
    </div>
  );
}
