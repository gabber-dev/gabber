/**
 * Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
 * SPDX-License-Identifier: SUL-1.0
 */

import { PlayIcon, StopIcon } from "@heroicons/react/24/solid";
import { useCallback, useMemo } from "react";
import { useRun } from "@/hooks/useRun";
import { useEditor } from "@/hooks/useEditor";

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
