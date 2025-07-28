/**
 * Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
 * SPDX-License-Identifier: SUL-1.0
 */

import React, { useState, useRef, useEffect } from "react";
import { JsonSchemaModal } from "./pads/property_edit/JsonSchemaModal";
import { Dialog, DialogBackdrop, DialogPanel } from "@headlessui/react";

type Props = {
  value: any;
  setValue: (value: any) => void;
};

export function ToolDefinitionProperty({ value, setValue }: Props) {
  const [schemaDialog, setSchemaDialog] = useState<"request" | null>(null);
  const schemaDialogRef = useRef<HTMLDialogElement>(null);

  useEffect(() => {
    const dialog = schemaDialogRef.current;
    if (schemaDialog && dialog) {
      dialog.showModal();
    } else if (dialog) {
      dialog.close();
    }
  }, [schemaDialog, value]);

  return (
    <div className="flex flex-col gap-6 p-4">
      <div className="space-y-6">
        <div>
          <label className="label">
            <span className="label-text text-neutral-600 dark:text-neutral-400">
              Name
            </span>
          </label>
          <input
            type="text"
            className="input input-bordered w-full"
            value={value.name}
            onChange={(e) => setValue?.({ ...value, name: e.target.value })}
          />
        </div>

        <div>
          <label className="label">
            <span className="label-text text-neutral-600 dark:text-neutral-400">
              Description
            </span>
          </label>
          <textarea
            className="textarea textarea-bordered w-full"
            rows={3}
            onChange={(e) =>
              setValue?.({ ...value, description: e.target.value })
            }
            value={value.description}
          />
        </div>

        <div>
          <div className="flex items-center justify-between mb-2">
            <label className="label">
              <span className="label-text text-neutral-600 dark:text-neutral-400">
                Request JSON Schema
              </span>
            </label>
            <button
              className="btn btn-primary btn-sm"
              onClick={() => setSchemaDialog("request")}
            >
              Edit Schema
            </button>
          </div>
        </div>

        <Dialog
          open={!!schemaDialog}
          onClose={() => {
            setSchemaDialog(null);
          }}
          className="relative z-10"
        >
          <DialogBackdrop
            transition
            className="fixed flex items-center justify-center inset-0 bg-black/75 transition-opacity"
          />
          <div className="fixed inset-0 z-10 w-screen overflow-y-auto">
            <div className="flex min-h-full items-end justify-center p-4 text-center sm:items-center sm:p-0">
              <DialogPanel
                transition
                className="relative transform overflow-hidden rounded-lg bg-base-200 border-base-content transition-all p-4"
              >
                <JsonSchemaModal
                  schema={
                    schemaDialog === "request"
                      ? value.request_schema
                      : value.response_schema
                  }
                  title={
                    schemaDialog === "request"
                      ? "Edit Request"
                      : "Edit Response"
                  }
                  setSchema={(newSchema: Record<string, any>) => {
                    if (schemaDialog === "request") {
                      setValue?.({ ...value, request_schema: newSchema });
                    } else {
                      setValue?.({ ...value, response_schema: newSchema });
                    }
                  }}
                />
              </DialogPanel>
            </div>
          </div>
        </Dialog>
      </div>
    </div>
  );
}
