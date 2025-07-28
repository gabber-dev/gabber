/**
 * Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
 * SPDX-License-Identifier: SUL-1.0
 */

"use client";

import toast from "react-hot-toast";
import React, { useState } from "react";
import {
  ChevronRightIcon,
  PlusIcon,
  ChevronDownIcon,
} from "@heroicons/react/24/outline";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useRepository } from "@/hooks/useRepository";

interface SubGraphModalProps {
  onClose: () => void;
}

function SubGraphModal({ onClose }: SubGraphModalProps) {
  const { saveSubGraph } = useRepository();
  const router = useRouter();
  const [name, setName] = useState("");

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-base-100 p-6 rounded-xl w-full max-w-md border-2 border-black border-b-4 border-r-4">
        <h3 className="font-bangers text-2xl mb-4">Create Sub Graph</h3>
        <div className="space-y-4">
          <div>
            <label className="block text-lg mb-2">
              What do you want to call your subgraph?
            </label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full px-4 py-2 bg-base-200 rounded border-2 border-black"
              placeholder="Enter subgraph name..."
              autoFocus
            />
          </div>
          <div className="flex justify-end space-x-3">
            <button
              onClick={onClose}
              className="px-4 py-2 rounded hover:bg-base-200"
            >
              Cancel
            </button>
            <button
              onClick={async () => {
                if (name.trim()) {
                  const newSubGraph = await saveSubGraph({
                    name,
                    graph: { nodes: [] },
                  });
                  onClose();
                  // Navigate to the newly created subgraph
                  router.push(`graph/${newSubGraph.id}`);
                } else {
                  toast.error("Sub graph name cannot be empty");
                }
              }}
              disabled={!name.trim()}
              className="px-4 py-2 bg-primary text-primary-content rounded hover:bg-primary-focus disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Create Sub Graph
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

export function SubGraphList() {
  const { subGraphs } = useRepository();
  const [showModal, setShowModal] = useState(false);
  const [subgraphsExpanded, setSubgraphsExpanded] = useState(false);

  const hasMoreThanFourSubgraphs = subGraphs.length > 4;
  const displayedSubgraphs = subgraphsExpanded
    ? subGraphs
    : subGraphs.slice(0, 4);

  const subgraphsContainerClass = subgraphsExpanded
    ? "max-h-[14rem] overflow-y-auto"
    : "max-h-none";

  return (
    <>
      <div className="mb-3">
        <div className="flex items-center justify-between mb-2">
          <h2 className="font-bangers text-2xl tracking-wider">Sub Graphs</h2>
          {subGraphs.length > 0 && (
            <button
              onClick={() => setShowModal(true)}
              className="btn btn-primary btn-sm font-vt323 text-lg tracking-wider"
            >
              <PlusIcon className="w-4 h-4 mr-2" />
              Add Subgraph
            </button>
          )}
        </div>
        <p className="text-sm text-base-content/70 mb-3">
          Create reusable nodes in the form of subgraphs that can be created and
          reused across your project&apos;s apps
        </p>
      </div>

      {subGraphs.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-8 border-2 border-dashed border-base-300 rounded-lg">
          <div className="text-center space-y-3">
            <p className="text-base-content/60">No subgraphs created yet</p>
            <button
              onClick={() => setShowModal(true)}
              className="btn btn-primary btn-sm font-bangers tracking-wider"
            >
              <PlusIcon className="w-4 h-4 mr-2" />
              Create Subgraph
            </button>
          </div>
        </div>
      ) : (
        <>
          <div className={`pr-2 ${subgraphsContainerClass}`}>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
              {displayedSubgraphs.map((sg) => {
                const isGabberSubgraph = !sg.project;
                const labelText = isGabberSubgraph ? "Gabber" : "Project";
                const labelColor = isGabberSubgraph
                  ? "bg-primary/20 text-primary border-primary/30"
                  : "bg-accent/20 text-accent border-accent/30";

                return (
                  <Link
                    key={sg.id}
                    href={`/graph/${sg.id}`}
                    className="relative overflow-visible card bg-base-200 hover:bg-base-300 border-2 border-black border-b-4 border-r-4 transform hover:translate-y-1 active:translate-y-2 transition-all group"
                  >
                    <div className="card-body p-4 relative">
                      {/* Label */}
                      <div className="absolute top-2 right-2">
                        <span
                          className={`px-2 py-1 rounded text-xs font-vt323 border ${labelColor}`}
                        >
                          {labelText}
                        </span>
                      </div>

                      <h3 className="font-vt323 text-xl text-base-content group-hover:text-warning tracking-wider transition-colors mb-3 pr-16">
                        {sg.name}
                      </h3>
                      <div className="flex items-center justify-between text-sm text-base-content/80">
                        <span className="flex items-center gap-1">
                          <ChevronRightIcon className="h-4 w-4 text-accent" />
                        </span>
                        <span className="flex items-center gap-1 text-warning">
                          Open
                          <ChevronRightIcon className="h-4 w-4" />
                        </span>
                      </div>
                    </div>
                  </Link>
                );
              })}
            </div>
          </div>
          {hasMoreThanFourSubgraphs && (
            <div className="flex justify-center mt-3">
              <button
                onClick={() => setSubgraphsExpanded(!subgraphsExpanded)}
                className="btn btn-ghost btn-sm gap-2 font-vt323"
              >
                {subgraphsExpanded ? (
                  <>
                    <ChevronDownIcon className="h-4 w-4 rotate-180" />
                    Show Less
                  </>
                ) : (
                  <>
                    <ChevronDownIcon className="h-4 w-4" />
                    {subGraphs.length <= 4
                      ? "Show More"
                      : `Show More (${subGraphs.length - 4} more)`}
                  </>
                )}
              </button>
            </div>
          )}
        </>
      )}

      {showModal && (
        <SubGraphModal
          onClose={() => {
            setShowModal(false);
          }}
        />
      )}
    </>
  );
}
