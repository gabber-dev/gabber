/**
 * Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
 * SPDX-License-Identifier: SUL-1.0
 */

import { useRun } from "@/hooks/useRun";
import toast from "react-hot-toast";

export function RunId() {
  const { runId } = useRun();

  if (!runId) {
    return null;
  }

  const handleCopy = async () => {
    if (navigator.clipboard) {
      toast.success("Run ID copied to clipboard");
      await navigator.clipboard.writeText(runId);
    }
  };

  return (
    <div className="relative flex items-center gap-1">
      <div className="text-xs">run_id:</div>
      <button
        onClick={handleCopy}
        className="btn btn-xs btn-ghost p-1 font-mono bg-base-200"
      >
        {runId}
      </button>
    </div>
  );
}
