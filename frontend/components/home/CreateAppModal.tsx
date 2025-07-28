/**
 * Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
 * SPDX-License-Identifier: SUL-1.0
 */

import { useRepository } from "@/hooks/useRepository";
import { useRouter } from "next/navigation";
import { useState } from "react";
import toast from "react-hot-toast";

export function CreateAppModal() {
  const { saveApp: createApp } = useRepository();
  const router = useRouter();
  const [appName, setAppName] = useState("");
  const [isOpen, setIsOpen] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (appName.trim()) {
      try {
        const newApp = await createApp({ name: appName, graph: { nodes: [] } });
        setAppName("");
        setIsOpen(false);
        // Navigate to the newly created app
        router.push(`app/${newApp.id}`);
      } catch (error) {
        toast.error("Error creating app. Please refresh.");
        console.error("Error creating app:", error);
        return;
      }
    }
  };

  return (
    <>
      {/* The modal */}
      <input
        type="checkbox"
        id="create-app-modal"
        className="modal-toggle"
        checked={isOpen}
        onChange={() => setIsOpen(!isOpen)}
      />
      <div className="modal" role="dialog">
        <div className="modal-box border">
          <h3 className="font-bold text-lg">Create New App</h3>
          <form onSubmit={handleSubmit} className="mt-4">
            <div className="form-control">
              <label className="label">
                <span className="label-text">App Name</span>
              </label>
              <input
                type="text"
                value={appName}
                onChange={(e) => setAppName(e.target.value)}
                placeholder="Enter app name"
                className="input input-bordered w-full"
                required
              />
            </div>
            <div className="modal-action">
              <button
                type="button"
                className="btn btn-ghost"
                onClick={() => setIsOpen(false)}
              >
                Cancel
              </button>
              <button type="submit" className="btn btn-primary">
                Create
              </button>
            </div>
          </form>
        </div>
        <label
          className="modal-backdrop m-0 p-0 w-full"
          onClick={() => setIsOpen(false)}
        ></label>
      </div>
    </>
  );
}
