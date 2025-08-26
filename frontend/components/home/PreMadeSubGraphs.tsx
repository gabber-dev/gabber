/**
 * Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
 * SPDX-License-Identifier: SUL-1.0
 */

import { RepositorySubGraph } from "@/generated/repository";
import { useRepository } from "@/hooks/useRepository";
import { CubeIcon, DocumentDuplicateIcon, ChevronRightIcon } from "@heroicons/react/24/solid";
import { useEffect, useState } from "react";
import toast from "react-hot-toast";
import { getPreMadeSubGraph } from "@/lib/repository";
import Link from "next/link";

export function PreMadeSubGraphs() {
  const { saveSubGraph, forceRefreshSubGraphs } = useRepository();
  const [preMadeSubGraphs, setPreMadeSubGraphs] = useState<RepositorySubGraph[]>([]);
  const [selectedSubGraphs, setSelectedSubGraphs] = useState<Set<string>>(new Set());
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadPreMadeSubGraphs = async () => {
      try {
        setLoading(true);
        // Load both premade subgraphs
        const [localLLM, services] = await Promise.all([
          getPreMadeSubGraph("conversational-local-llm"),
          getPreMadeSubGraph("conversational-services")
        ]);
        setPreMadeSubGraphs([localLLM, services]);
      } catch (error) {
        console.error("Error loading premade subgraphs:", error);
        toast.error("Failed to load premade subgraphs");
      } finally {
        setLoading(false);
      }
    };

    loadPreMadeSubGraphs();
  }, []);

  const handleCopySelected = async () => {
    const selectedArray = Array.from(selectedSubGraphs);
    const confirmed = window.confirm(
      `Copy ${selectedArray.length} subgraph${selectedArray.length > 1 ? "s" : ""} to your collection?`
    );
    if (!confirmed) return;

    // Copy all selected subgraphs
    for (const subGraphId of selectedArray) {
      const subGraph = preMadeSubGraphs.find(sg => sg.id === subGraphId);
      if (subGraph) {
        try {
          const newName = `${subGraph.name} (Copy)`;
          await saveSubGraph({
            name: newName,
            graph: subGraph.graph
          });
        } catch (error) {
          console.error("Error copying subgraph:", error);
          toast.error(`Failed to copy ${subGraph.name}`);
        }
      }
    }
    setSelectedSubGraphs(new Set());

    // Force refresh the subgraphs list to show the newly copied items
    await forceRefreshSubGraphs();

    toast.success("Subgraphs copied successfully!");
  };

  if (loading) {
    return (
      <div className="relative w-full">
        <div>
          <div className="flex items-center justify-between mb-3">
            <h2 className="font-bangers text-2xl tracking-wider">Pre-made Sub Graphs</h2>
          </div>
          <div className="border-2 border-black border-b-4 border-r-4 rounded-xl p-4 bg-base-200">
            <div className="flex justify-center items-center py-8">
              <div className="loading loading-spinner loading-lg"></div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="relative w-full">
      <div>
        <div className="flex items-center justify-between mb-3">
          <h2 className="font-bangers text-2xl tracking-wider">Pre-made Sub Graphs</h2>
          {selectedSubGraphs.size > 0 && (
            <div className="flex gap-2">
              <button
                onClick={handleCopySelected}
                className="btn btn-warning btn-sm gap-2 font-vt323"
              >
                <DocumentDuplicateIcon className="h-4 w-4" />
                Copy {selectedSubGraphs.size} to My Subgraphs
              </button>
            </div>
          )}
        </div>
        <div className="border-2 border-black border-b-4 border-r-4 rounded-xl p-4 bg-base-200">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
            {preMadeSubGraphs.map((subGraph) => (
              <Link
                key={subGraph.id}
                href={`/graph/${subGraph.id}`}
                className="relative overflow-visible card bg-base-200 hover:bg-base-300 border-2 border-black border-b-4 border-r-4 transform hover:translate-y-1 active:translate-y-2 transition-all group"
              >
                <div className="card-body p-4 relative">
                  {/* Selection checkbox */}
                  <div
                    className={`absolute top-2 left-2 z-10 w-5 h-5 rounded border-2 border-warning cursor-pointer transition-all duration-200 ${
                      selectedSubGraphs.has(subGraph.id) ? "bg-warning" : "hover:bg-warning/10"
                    }`}
                    onClick={(e) => {
                      e.preventDefault();
                      e.stopPropagation();
                      setSelectedSubGraphs((prev) => {
                        const newSet = new Set(prev);
                        if (newSet.has(subGraph.id)) {
                          newSet.delete(subGraph.id);
                        } else {
                          newSet.add(subGraph.id);
                        }
                        return newSet;
                      });
                    }}
                  >
                    <input
                      type="checkbox"
                      checked={selectedSubGraphs.has(subGraph.id)}
                      onChange={() => {}}
                      className="sr-only"
                    />
                    {selectedSubGraphs.has(subGraph.id) && (
                      <div className="absolute inset-0 flex items-center justify-center text-warning-content">
                        <svg
                          xmlns="http://www.w3.org/2000/svg"
                          className="h-3 w-3"
                          viewBox="0 0 20 20"
                          fill="currentColor"
                        >
                          <path
                            fillRule="evenodd"
                            d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                            clipRule="evenodd"
                          />
                        </svg>
                      </div>
                    )}
                  </div>

                  <h3 className="font-vt323 text-xl text-base-content group-hover:text-warning tracking-wider transition-colors mb-3">
                    {subGraph.name}
                  </h3>
                  <div className="flex items-center justify-between text-sm text-base-content/80">
                    <span className="flex items-center gap-1">
                      <CubeIcon className="h-4 w-4 text-accent" />
                      Template
                    </span>
                    <span className="flex items-center gap-1 text-warning">
                      Open
                      <ChevronRightIcon className="h-4 w-4" />
                    </span>
                  </div>
                </div>
              </Link>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
