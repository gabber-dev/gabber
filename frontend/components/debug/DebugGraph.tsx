/**
 * Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
 * SPDX-License-Identifier: SUL-1.0
 */

import { ReactFlowProvider } from "@xyflow/react";
import { FlowEdit } from "../flow/FlowEdit";
import { useRun } from "@/hooks/useRun";
import { useEffect } from "react";
import { BottomBar } from "../app_edit/BottomBar";

export function DebugGraph() {
  return (
    <ReactFlowProvider>
      <DebugGraphInner />
    </ReactFlowProvider>
  );
}

function DebugGraphInner() {
  const { startRun } = useRun();

  useEffect(() => {
    // Automatically start the run when the component mounts. Empty graph because
    // we are in debug mode and the graph is not editable. It's already included in
    // startRunImpl.
    startRun({ graph: { nodes: [] } });
  }, [startRun]);
  return (
    <div className="relative w-full h-full">
      <div className="absolute top-0 left-0 right-0 bottom-16">
        <FlowEdit editable={false} />;
      </div>
      <div className="absolute bottom-0 left-0 right-0 h-16">
        <BottomBar
          logButtonEnabled={false}
          saveButtonEnabled={false}
          debugControlsEnabled={false}
        />
      </div>
    </div>
  );
}
