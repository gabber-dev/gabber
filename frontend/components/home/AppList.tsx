/**
 * Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
 * SPDX-License-Identifier: SUL-1.0
 */
"use client";

import { useRepository } from "@/hooks/useRepository";
import {
  ChevronDownIcon,
  TrashIcon,
  DocumentDuplicateIcon,
  PencilIcon,
} from "@heroicons/react/24/solid";
import { useCallback, useRef, useState } from "react";
import { AppListItem } from "./AppListItem";
import ReactModal from "react-modal";
import { CreateAppModal } from "./CreateAppModal";
import toast from "react-hot-toast";

export function AppList() {
  const [showModal, setShowModal] = useState(false);
  const [appsExpanded, setAppsExpanded] = useState(false);
  const { apps, deleteApp, saveApp, refreshApps, importApp } = useRepository();
  const [selectedApps, setSelectedApps] = useState<Set<string>>(new Set());
  const [renameModal, setRenameModal] = useState<{
    isOpen: boolean;
    appId: string;
    currentName: string;
  }>({ isOpen: false, appId: "", currentName: "" });
  const fileInputRef = useRef<HTMLInputElement>(null);

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

  const handleDuplicateSelected = async () => {
    const confirmed = window.confirm(
      `Duplicate ${selectedApps.size} app${selectedApps.size > 1 ? "s" : ""} to your collection?`,
    );
    if (!confirmed) return;

    // Duplicate all selected apps
    for (const appId of selectedApps) {
      const app = apps.find((a) => a.id === appId);
      if (app) {
        try {
          await saveApp({
            name: `${app.name} (Copy)`,
            graph: app.graph,
          });
        } catch (error) {
          console.error("Error duplicating app:", error);
          toast.error(`Failed to duplicate ${app.name}`);
        }
      }
    }
    setSelectedApps(new Set());

    // Refresh the apps list to show the newly duplicated items
    await refreshApps();

    toast.success("Apps duplicated successfully!");
  };

  const handleRenameApp = async (appId: string, newName: string) => {
    try {
      const app = apps.find((a) => a.id === appId);
      if (!app) return;

      await saveApp({
        id: appId,
        name: newName,
        graph: app.graph,
      });

      toast.success("App renamed successfully!");
      setRenameModal({ isOpen: false, appId: "", currentName: "" });
    } catch (error) {
      toast.error("Failed to rename app");
      console.error("Error renaming app:", error);
    }
  };

  const openRenameModal = (appId: string, currentName: string) => {
    setRenameModal({ isOpen: true, appId, currentName });
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
          await importApp(JSON.parse(fileContent));
          await refreshApps();
        }
      } catch (error) {
        console.error("Error importing app:", error);
        toast.error("Failed to import app");
      }
    },
    [importApp, refreshApps],
  );

  const hasMoreThanFourApps = apps.length > 4;
  const displayedApps = appsExpanded ? apps : apps.slice(0, 4);

  const appsContainerClass = appsExpanded
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
        <CreateAppModal />
      </ReactModal>

      {/* Rename Modal */}
      <ReactModal
        isOpen={renameModal.isOpen}
        onRequestClose={() =>
          setRenameModal({ isOpen: false, appId: "", currentName: "" })
        }
        overlayClassName="fixed top-0 bottom-0 left-0 right-0 backdrop-blur-lg bg-blur flex justify-center items-center z-50"
        className="w-full max-w-md bg-neutral-800 rounded-lg shadow-lg outline-none z-50"
        shouldCloseOnOverlayClick={true}
      >
        <div className="p-6">
          <h3 className="font-bangers text-xl mb-4">Rename App</h3>
          <form
            onSubmit={(e) => {
              e.preventDefault();
              const formData = new FormData(e.target as HTMLFormElement);
              const newName = formData.get("name") as string;
              if (newName.trim()) {
                handleRenameApp(renameModal.appId, newName.trim());
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
                  setRenameModal({ isOpen: false, appId: "", currentName: "" })
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
            <h2 className="font-bangers text-2xl tracking-wider">Your Apps</h2>
            <button
              onClick={handleImportClick}
              className="btn btn-accent btn-sm"
            >
              Import
            </button>
          </div>
          <button className="btn" onClick={() => setShowModal(true)}>
            Create App
          </button>
          {selectedApps.size > 0 && (
            <div className="flex gap-2">
              <button
                onClick={handleDuplicateSelected}
                className="btn btn-warning btn-sm gap-2 font-vt323"
              >
                <DocumentDuplicateIcon className="h-4 w-4" />
                Duplicate {selectedApps.size}
              </button>
              <button
                onClick={() => {
                  if (selectedApps.size === 1) {
                    const appId = Array.from(selectedApps)[0];
                    const app = apps.find((a) => a.id === appId);
                    if (app) {
                      openRenameModal(appId, app.name);
                    }
                  }
                }}
                disabled={selectedApps.size !== 1}
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
