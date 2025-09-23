/**
 * Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
 * SPDX-License-Identifier: SUL-1.0
 */

import { useRepository } from "@/hooks/useRepository";
import { useRouter } from "next/navigation";
import { useState } from "react";
import toast from "react-hot-toast";

export function CreateAppModal() {
  const { saveApp, appEditPath } = useRepository();
  const router = useRouter();
  const [appName, setAppName] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (appName.trim()) {
      try {
        const newApp = await saveApp({ name: appName, graph: { nodes: [] } });
        setAppName("");
        // Navigate to the newly created app
        router.push(appEditPath(newApp.id));
      } catch (error) {
        toast.error("Error creating app. Please refresh.");
        console.error("Error creating app:", error);
        return;
      }
    }
  };

  return (
    <div className="card p-2 bg-neutral-800">
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
          <button type="submit" className="btn btn-primary">
            Create
          </button>
        </div>
      </form>
    </div>
  );
}
