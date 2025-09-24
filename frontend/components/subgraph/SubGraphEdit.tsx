/**
 * Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
 * SPDX-License-Identifier: SUL-1.0
 */

import { ReactFlowProvider } from "@xyflow/react";
import { FlowEdit } from "../flow/FlowEdit";
import { BottomBar } from "../app_edit/BottomBar";

type Props = {
  editable: boolean;
};

export function SubGraphEdit(props: Props) {
  return (
    <ReactFlowProvider>
      <SubGraphEditInner {...props} />
    </ReactFlowProvider>
  );
}

function SubGraphEditInner({ editable }: Props) {
  return (
    <div className="relative w-full h-full">
      <div
        className={`absolute top-0 left-0 right-0 ${editable ? "bottom-16" : "bottom-0"}`}
      >
        <FlowEdit editable={editable} />;
      </div>
      {editable && (
        <div className="absolute bottom-0 left-0 right-0 h-16">
          <BottomBar
            saveButtonEnabled={true}
            logButtonEnabled={false}
            debugControlsEnabled={false}
          />
        </div>
      )}
    </div>
  );
}
