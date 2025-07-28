/**
 * Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
 * SPDX-License-Identifier: SUL-1.0
 */

import { RepositoryApp } from "@/generated/repository";
import { ChevronRightIcon, CubeIcon } from "@heroicons/react/24/solid";
import Link from "next/link";

export function AppListItem({
  app,
  isSelected,
  onSelect,
}: {
  app: RepositoryApp;
  isSelected: boolean;
  onSelect: (selected: boolean) => void;
}) {
  const handleSelect = (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    onSelect(!isSelected);
  };

  return (
    <Link
      href={`/app/${app.id}`}
      className="relative overflow-visible card bg-base-200 hover:bg-base-300 border-2 border-black border-b-4 border-r-4 transform hover:translate-y-1 active:translate-y-2 transition-all group"
    >
      <div className="card-body p-4 relative">
        {/* Selection checkbox */}
        <div
          className={`absolute top-2 right-2 z-10 w-5 h-5 rounded border-2 border-warning cursor-pointer transition-all duration-200 ${
            isSelected ? "bg-warning" : "hover:bg-warning/10"
          }`}
          onClick={handleSelect}
        >
          <input
            type="checkbox"
            checked={isSelected}
            onChange={() => {}}
            className="sr-only"
          />
          {isSelected && (
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
          {app.name}
        </h3>
        <div className="flex items-center justify-between text-sm text-base-content/80">
          <span className="flex items-center gap-1">
            <CubeIcon className="h-4 w-4 text-accent" />
          </span>
          <span className="flex items-center gap-1 text-warning">
            Open
            <ChevronRightIcon className="h-4 w-4" />
          </span>
        </div>
      </div>
    </Link>
  );
}
