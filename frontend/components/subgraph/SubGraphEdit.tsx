/**
 * Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
 * SPDX-License-Identifier: SUL-1.0
 */

import { ReactFlowProvider } from "@xyflow/react";
import { FlowEdit } from "../flow/FlowEdit";
import { BottomBar } from "./BottomBar";

export function SubGraphEdit() {
  return (
    <ReactFlowProvider>
      <SubGraphEditInner />
    </ReactFlowProvider>
  );
}

function SubGraphEditInner() {
  return (
    <div className="relative w-full h-full">
      <div className="absolute top-0 left-0 right-0 bottom-16">
        <FlowEdit />;
      </div>
      <div className="absolute bottom-0 left-0 right-0 h-16">
        <BottomBar />
      </div>
    </div>
  );
}
