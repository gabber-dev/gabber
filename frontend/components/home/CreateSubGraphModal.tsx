/**
 * Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
 * SPDX-License-Identifier: SUL-1.0
 */

import { useRepository } from "@/hooks/useRepository";
import { useRouter } from "next/navigation";
import { useState } from "react";
import toast from "react-hot-toast";

export function CreateSubGraphModal() {
  const { saveSubGraph } = useRepository();
  const router = useRouter();
  const [name, setName] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (name.trim()) {
      try {
        const newSubGraph = await saveSubGraph({
          name: name,
          graph: { nodes: [] },
        });
        setName("");
        // Navigate to the newly created app
        router.push(`graph/${newSubGraph.id}`);
      } catch (error) {
        toast.error("Error creating subgraph. Please refresh.");
        console.error("Error creating subgraph:", error);
        return;
      }
    }
  };

  return (
    <div className="card p-2 bg-neutral-800">
      <h3 className="font-bold text-lg">Create New SubGraph</h3>
      <form onSubmit={handleSubmit} className="mt-4">
        <div className="form-control">
          <label className="label">
            <span className="label-text">SubGraph Name</span>
          </label>
          <input
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
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
