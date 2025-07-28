/**
 * Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
 * SPDX-License-Identifier: SUL-1.0
 */

import { useEditor } from "@/hooks/useEditor";

export function BottomBar() {
  const { unsavedChanges, saveChanges, saving } = useEditor();

  return (
    <div className="w-full h-full bg-base-200 border-t border-base-300 z-30 h-16">
      <div className="h-full flex items-center justify-between px-4">
        <div className="flex-1 flex justify-center">
          {unsavedChanges && (
            <div className="flex items-center gap-3 bg-warning/10 border border-warning/20 rounded-lg px-4 py-2">
              <div className="w-2 h-2 bg-warning rounded-full animate-pulse"></div>
              <span className="text-sm font-medium text-warning-content">
                Unsaved changes
              </span>
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
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
