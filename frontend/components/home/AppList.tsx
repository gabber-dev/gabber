/**
 * Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
 * SPDX-License-Identifier: SUL-1.0
 */

import { useRepository } from "@/hooks/useRepository";
import { ChevronDownIcon, TrashIcon } from "@heroicons/react/24/solid";
import { useState } from "react";
import { AppListItem } from "./AppListItem";
import ReactModal from "react-modal";
import { CreateAppModal } from "./CreateAppModal";

export function AppList() {
  const [showModal, setShowModal] = useState(false);
  const [appsExpanded, setAppsExpanded] = useState(false);
  const { apps, deleteApp } = useRepository();
  const [selectedApps, setSelectedApps] = useState<Set<string>>(new Set());

  const handleDeleteSelected = async () => {
    const confirmed = window.confirm(
      `Are you sure you want to delete ${selectedApps.size} app${selectedApps.size > 1 ? "s" : ""}? This cannot be undone.`,
    );
    if (!confirmed) return;

    // Delete all selected apps
    for (const appId of selectedApps) {
      await deleteApp(appId);
    }
    setSelectedApps(new Set());
  };
  const hasMoreThanFourApps = apps.length > 4;
  const displayedApps = appsExpanded ? apps : apps.slice(0, 4);

  const appsContainerClass = appsExpanded
    ? "max-h-[14rem] overflow-y-auto"
    : "max-h-none";
  return (
    <div className="relative space-y-6 w-full h-full">
      <div ref={(el) => ReactModal.setAppElement(el as HTMLElement)} />
      <ReactModal
        isOpen={showModal}
        onRequestClose={() => setShowModal(false)}
        overlayClassName="fixed top-0 bottom-0 left-0 right-0 backdrop-blur-lg bg-blur flex justify-center items-center"
        className="w-full max-w-lg bg-white dark:bg-neutral-800 rounded-lg shadow-lg outline-none"
        shouldCloseOnOverlayClick={true}
      >
        <CreateAppModal />
      </ReactModal>
      <div>
        <div className="flex items-center justify-between mb-3">
          <h2 className="font-bangers text-2xl tracking-wider">Your Apps</h2>
          <button className="btn" onClick={() => setShowModal(true)}>
            Create App
          </button>
          {selectedApps.size > 0 && (
            <div className="flex gap-2">
              <button
                onClick={handleDeleteSelected}
                className="btn btn-error btn-sm gap-2 font-vt323"
              >
                <TrashIcon className="h-4 w-4" />
                Delete {selectedApps.size}
              </button>
            </div>
          )}
        </div>
        <div className="border-2 border-black border-b-4 border-r-4 rounded-xl p-4 bg-base-200">
          <div className={`pr-2 ${appsContainerClass}`}>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
              {displayedApps.map((app) => (
                <AppListItem
                  key={app.id}
                  app={app}
                  isSelected={selectedApps.has(app.id)}
                  onSelect={(selected) => {
                    setSelectedApps((prev) => {
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
                onClick={() => setAppsExpanded(!appsExpanded)}
                className="btn btn-ghost btn-sm gap-2 font-vt323"
              >
                {appsExpanded ? (
                  <>
                    <ChevronDownIcon className="h-4 w-4 rotate-180" />
                    Show Less
                  </>
                ) : (
                  <>
                    <ChevronDownIcon className="h-4 w-4" />
                    Show More ({apps.length - 4} more)
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
