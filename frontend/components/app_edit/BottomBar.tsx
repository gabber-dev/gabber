/**
 * Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
 * SPDX-License-Identifier: SUL-1.0
 */

import { useEditor } from "@/hooks/useEditor";
import { DebugControls } from "../PlayButton";

type Props = {
  logButtonEnabled: boolean;
  saveButtonEnabled: boolean;
  debugControlsEnabled: boolean;
};

export function BottomBar({
  logButtonEnabled,
  saveButtonEnabled,
  debugControlsEnabled,
}: Props) {
  const { unsavedChanges, saveChanges, saving, logsShowing, setLogsShowing } =
    useEditor();

  return (
    <div className="w-full h-16 bg-base-200 border-t border-base-300 z-30">
      <div className="h-full grid grid-cols-3 items-center px-4">
        <div>{debugControlsEnabled && <DebugControls />}</div>

        <div className="flex justify-center items-center">
          {unsavedChanges && (
            <div className="flex items-center gap-3 bg-warning/10 border border-warning/20 rounded-lg px-4 py-2">
              <div className="w-2 h-2 bg-warning rounded-full animate-pulse"></div>
              <span className="text-sm font-medium text-warning-content">
                Unsaved changes
              </span>
              {saveButtonEnabled && (
                <button
                  className="btn btn-warning btn-sm"
                  onClick={saveChanges}
                  disabled={saving}
                >
                  {saving ? (
                    <div className="loading loading-dots loading-sm" />
                  ) : (
                    "Save"
                  )}
                </button>
              )}
            </div>
          )}
        </div>
        <div className="flex justify-end">
          {logButtonEnabled && (
            <button
              className="btn btn-sm"
              onClick={() => setLogsShowing(!logsShowing)}
            >
              Log
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
