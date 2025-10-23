/**
 * Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
 * SPDX-License-Identifier: SUL-1.0
 */

import { useRepository } from "@/hooks/useRepository";
import {
  ChevronDownIcon,
  TrashIcon,
  DocumentDuplicateIcon,
  PencilIcon,
  ArrowDownTrayIcon,
  ArrowUpTrayIcon,
} from "@heroicons/react/24/solid";
import { useCallback, useRef, useState } from "react";
import ReactModal from "react-modal";
import { CreateSubGraphModal } from "./CreateSubGraphModal";
import { SubGraphListItem } from "./SubGraphListItem";
import toast from "react-hot-toast";

export function SubGraphList() {
  const [showModal, setShowModal] = useState(false);
  const [subGraphsExpanded, setSubGraphsExpanded] = useState(false);
  const {
    subGraphs,
    deleteSubGraph,
    saveSubGraph,
    refreshSubGraphs,
    importSubGraph,
    exportSubGraph,
  } = useRepository();
  const [selectedSubGraphs, setSelectedSubGraphs] = useState<Set<string>>(
    new Set(),
  );
  const [renameModal, setRenameModal] = useState<{
    isOpen: boolean;
    subGraphId: string;
    currentName: string;
  }>({ isOpen: false, subGraphId: "", currentName: "" });
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleDeleteSelected = async () => {
    const confirmed = window.confirm(
      `Are you sure you want to delete ${selectedSubGraphs.size} subgraph${selectedSubGraphs.size > 1 ? "s" : ""}? This cannot be undone.`,
    );
    if (!confirmed) return;

    // Delete all selected subgraphs
    for (const subGraphId of selectedSubGraphs) {
      await deleteSubGraph(subGraphId);
    }
    setSelectedSubGraphs(new Set());
  };

  const handleDuplicateSelected = async () => {
    const confirmed = window.confirm(
      `Duplicate ${selectedSubGraphs.size} subgraph${selectedSubGraphs.size > 1 ? "s" : ""} to your collection?`,
    );
    if (!confirmed) return;

    // Duplicate all selected subgraphs
    for (const subGraphId of selectedSubGraphs) {
      const subGraph = subGraphs.find((sg) => sg.id === subGraphId);
      if (subGraph) {
        try {
          await saveSubGraph({
            name: `${subGraph.name} (Copy)`,
            graph: subGraph.graph,
          });
        } catch (error) {
          console.error("Error duplicating subgraph:", error);
          toast.error(`Failed to duplicate ${subGraph.name}`);
        }
      }
    }
    setSelectedSubGraphs(new Set());

    // Refresh the subgraphs list to show the newly duplicated items
    await refreshSubGraphs();

    toast.success("Subgraphs duplicated successfully!");
  };

  const handleRenameSubGraph = async (subGraphId: string, newName: string) => {
    try {
      const subGraph = subGraphs.find((sg) => sg.id === subGraphId);
      if (!subGraph) return;

      await saveSubGraph({
        id: subGraphId,
        name: newName,
        graph: subGraph.graph,
      });

      toast.success("Subgraph renamed successfully!");
      setRenameModal({ isOpen: false, subGraphId: "", currentName: "" });
    } catch (error) {
      toast.error("Failed to rename subgraph");
      console.error("Error renaming subgraph:", error);
    }
  };

  const openRenameModal = (subGraphId: string, currentName: string) => {
    setRenameModal({ isOpen: true, subGraphId, currentName });
  };

  const handleExportSelected = async () => {
    if (selectedSubGraphs.size === 0) {
      toast.error("Please select at least one subgraph to export");
      return;
    }

    let successCount = 0;
    let failureCount = 0;

    toast.success("Starting export...");

    // Export each selected subgraph with a delay to avoid browser blocking
    for (const subGraphId of selectedSubGraphs) {
      const subGraph = subGraphs.find((sg) => sg.id === subGraphId);

      if (!subGraph) {
        failureCount++;
        continue;
      }

      try {
        const subGraphExport = await exportSubGraph(subGraphId);
        const blob = new Blob([JSON.stringify(subGraphExport, null, 2)], {
          type: "application/json",
        });
        const url = URL.createObjectURL(blob);
        const link = document.createElement("a");
        link.href = url;
        link.download = `${subGraphExport.subgraph.name || "subgraph"}.json`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(url);
        successCount++;

        // Add a small delay between downloads to avoid browser blocking
        if (selectedSubGraphs.size > 1) {
          await new Promise((resolve) => setTimeout(resolve, 500));
        }
      } catch (error) {
        console.error(`Error exporting subgraph ${subGraph.name}:`, error);
        failureCount++;
      }
    }

    // Show results after a delay to let downloads start
    setTimeout(() => {
      if (successCount > 0) {
        if (failureCount === 0) {
          toast.success(
            `Successfully exported ${successCount} subgraph${successCount > 1 ? "s" : ""}!`,
          );
        } else {
          toast.success(
            `Exported ${successCount} subgraph${successCount > 1 ? "s" : ""} successfully (${
              failureCount
            } failed)`,
          );
        }
      } else {
        toast.error(
          `Failed to export ${failureCount} subgraph${failureCount > 1 ? "s" : ""}`,
        );
      }
    }, 1000);
  };

  const handleImportClick = useCallback(() => {
    fileInputRef.current?.click();
  }, []);

  const handleFileChange = useCallback(
    async (e: React.ChangeEvent<HTMLInputElement>) => {
      try {
        const file = e.target.files?.[0];
        if (file && file.type === "application/json") {
          const fileContent = await file.text();
          await importSubGraph(JSON.parse(fileContent));
          await refreshSubGraphs();
        }
      } catch (error) {
        console.error("Error importing subgraph:", error);
        toast.error("Failed to import subgraph");
      }
    },
    [importSubGraph, refreshSubGraphs],
  );

  const hasMoreThanFourApps = subGraphs.length > 4;
  const displayedSubGraphs = subGraphsExpanded
    ? subGraphs
    : subGraphs.slice(0, 4);

  const containerClass = subGraphsExpanded
    ? "max-h-[14rem] overflow-y-auto"
    : "max-h-none";
  return (
    <div className="relative w-full">
      <div ref={(el) => ReactModal.setAppElement(el as HTMLElement)} />
      <ReactModal
        isOpen={showModal}
        onRequestClose={() => setShowModal(false)}
        overlayClassName="fixed top-0 bottom-0 left-0 right-0 backdrop-blur-lg bg-blur flex justify-center items-center z-50"
        className="w-full max-w-lg bg-neutral-800 rounded-lg shadow-lg outline-none z-50"
        shouldCloseOnOverlayClick={true}
      >
        <CreateSubGraphModal />
      </ReactModal>

      {/* Rename Modal */}
      <ReactModal
        isOpen={renameModal.isOpen}
        onRequestClose={() =>
          setRenameModal({ isOpen: false, subGraphId: "", currentName: "" })
        }
        overlayClassName="fixed top-0 bottom-0 left-0 right-0 backdrop-blur-lg bg-blur flex justify-center items-center z-50"
        className="w-full max-w-md bg-neutral-800 rounded-lg shadow-lg outline-none z-50"
        shouldCloseOnOverlayClick={true}
      >
        <div className="p-6">
          <h3 className="font-bangers text-xl mb-4">Rename Subgraph</h3>
          <form
            onSubmit={(e) => {
              e.preventDefault();
              const formData = new FormData(e.target as HTMLFormElement);
              const newName = formData.get("name") as string;
              if (newName.trim()) {
                handleRenameSubGraph(renameModal.subGraphId, newName.trim());
              }
            }}
          >
            <div className="form-control mb-4">
              <label className="label">
                <span className="label-text">New Name</span>
              </label>
              <input
                type="text"
                name="name"
                defaultValue={renameModal.currentName}
                className="input input-bordered"
                required
                autoFocus
              />
            </div>
            <div className="flex gap-2 justify-end">
              <button
                type="button"
                onClick={() =>
                  setRenameModal({
                    isOpen: false,
                    subGraphId: "",
                    currentName: "",
                  })
                }
                className="btn btn-ghost"
              >
                Cancel
              </button>
              <button type="submit" className="btn btn-primary">
                Rename
              </button>
            </div>
          </form>
        </div>
      </ReactModal>

      <div>
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <h2 className="font-bangers text-2xl tracking-wider">
              Your Sub Graphs
            </h2>
            <button
              onClick={handleImportClick}
              title="Import subgraph from JSON file"
              className="btn btn-sm gap-2 font-vt323 tracking-wider btn-primary group overflow-hidden transition-all duration-300 ease-in-out relative flex items-center justify-center w-20"
            >
              <ArrowDownTrayIcon className="h-4 w-4 flex-shrink-0 absolute left-1/2 top-1/2 transform -translate-x-1/2 -translate-y-1/2 opacity-0 group-hover:opacity-100 transition-opacity duration-300 ease-in-out" />
              <span className="opacity-100 group-hover:opacity-0 transition-opacity duration-300 ease-in-out whitespace-nowrap">
                Import
              </span>
            </button>
          </div>
          {selectedSubGraphs.size === 0 && (
            <button className="btn" onClick={() => setShowModal(true)}>
              Create Sub Graph
            </button>
          )}
          {selectedSubGraphs.size > 0 && (
            <div className="flex gap-2">
              <button
                onClick={handleDuplicateSelected}
                className="btn btn-warning btn-sm gap-2 font-vt323"
              >
                <DocumentDuplicateIcon className="h-4 w-4" />
                Duplicate {selectedSubGraphs.size}
              </button>
              <button
                onClick={handleExportSelected}
                className="btn btn-primary btn-sm gap-2 font-vt323"
              >
                <ArrowUpTrayIcon className="h-4 w-4" />
                Export {selectedSubGraphs.size}
              </button>
              <button
                onClick={() => {
                  if (selectedSubGraphs.size === 1) {
                    const subGraphId = Array.from(selectedSubGraphs)[0];
                    const subGraph = subGraphs.find(
                      (sg) => sg.id === subGraphId,
                    );
                    if (subGraph) {
                      openRenameModal(subGraphId, subGraph.name);
                    }
                  }
                }}
                disabled={selectedSubGraphs.size !== 1}
                className="btn btn-info btn-sm gap-2 font-vt323"
              >
                <PencilIcon className="h-4 w-4" />
                Rename
              </button>
              <button
                onClick={handleDeleteSelected}
                className="btn btn-error btn-sm gap-2 font-vt323"
              >
                <TrashIcon className="h-4 w-4" />
                Delete {selectedSubGraphs.size}
              </button>
            </div>
          )}
        </div>
        <div className="border-2 border-black border-b-4 border-r-4 rounded-xl p-4 bg-base-200">
          {subGraphs.length === 0 ? (
            <div className="flex items-center justify-center py-8 text-center">
              <p className="text-base-content/60 font-vt323 text-lg">
                No subgraphs yet.
                <button
                  onClick={() => setShowModal(true)}
                  className="link link-primary mx-1 font-vt323"
                >
                  Create one
                </button>
                to condense common node configurations into single nodes.
              </p>
            </div>
          ) : (
            <div className={`pr-2 ${containerClass}`}>
              <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
                {displayedSubGraphs.map((app) => (
                  <SubGraphListItem
                    key={app.id}
                    app={app}
                    isSelected={selectedSubGraphs.has(app.id)}
                    onSelect={(selected) => {
                      setSelectedSubGraphs((prev) => {
                        const newSet = new Set(prev);
                        if (selected) {
                          newSet.add(app.id);
                        } else {
                          newSet.delete(app.id);
                        }
                        return newSet;
                      });
                    }}
                  />
                ))}
              </div>
            </div>
          )}
          {hasMoreThanFourApps && (
            <div className="flex justify-center mt-3">
              <button
                onClick={() => setSubGraphsExpanded(!subGraphsExpanded)}
                className="btn btn-ghost btn-sm gap-2 font-vt323"
              >
                {subGraphsExpanded ? (
                  <>
                    <ChevronDownIcon className="h-4 w-4 rotate-180" />
                    Show Less
                  </>
                ) : (
                  <>
                    <ChevronDownIcon className="h-4 w-4" />
                    Show More ({subGraphs.length - 4} more)
                  </>
                )}
              </button>
            </div>
          )}
        </div>
      </div>
      <input
        type="file"
        accept=".json"
        ref={fileInputRef}
        className="hidden"
        onChange={handleFileChange}
      />
    </div>
  );
}
