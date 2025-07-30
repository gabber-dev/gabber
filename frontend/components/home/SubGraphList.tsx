/**
 * Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
 * SPDX-License-Identifier: SUL-1.0
 */

import { useRepository } from "@/hooks/useRepository";
import { ChevronDownIcon, TrashIcon } from "@heroicons/react/24/solid";
import { useState } from "react";
import { AppListItem } from "./AppListItem";
import ReactModal from "react-modal";
import { CreateSubGraphModal } from "./CreateSubGraphModal";
import { SubGraphListItem } from "./SubGraphListItem";

export function SubGraphList() {
  const [showModal, setShowModal] = useState(false);
  const [subGraphsExpanded, setSubGraphsExpanded] = useState(false);
  const { subGraphs, deleteSubGraph } = useRepository();
  const [selectedSubGraphs, setSelectedSubGraphs] = useState<Set<string>>(
    new Set(),
  );

  const handleDeleteSelected = async () => {
    const confirmed = window.confirm(
      `Are you sure you want to delete ${selectedSubGraphs.size} app${selectedSubGraphs.size > 1 ? "s" : ""}? This cannot be undone.`,
    );
    if (!confirmed) return;

    // Delete all selected apps
    for (const appId of selectedSubGraphs) {
      await deleteSubGraph(appId);
    }
    setSelectedSubGraphs(new Set());
  };
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
        overlayClassName="fixed top-0 bottom-0 left-0 right-0 backdrop-blur-lg bg-blur flex justify-center items-center"
        className="w-full max-w-lg bg-white dark:bg-neutral-800 rounded-lg shadow-lg outline-none"
        shouldCloseOnOverlayClick={true}
      >
        <CreateSubGraphModal />
      </ReactModal>
      <div>
        <div className="flex items-center justify-between mb-3">
          <h2 className="font-bangers text-2xl tracking-wider">
            Your Sub Graphs
          </h2>
          <button className="btn" onClick={() => setShowModal(true)}>
            Create Sub Graph
          </button>
          {selectedSubGraphs.size > 0 && (
            <div className="flex gap-2">
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
    </div>
  );
}
