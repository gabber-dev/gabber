/**
 * Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
 * SPDX-License-Identifier: SUL-1.0
 */

import { useRepository } from "@/hooks/useRepository";
import { BeakerIcon, ChevronRightIcon } from "@heroicons/react/24/solid";
import Link from "next/link";

export function ExampleList() {
  const { examples } = useRepository();

  return (
    <div className="relative w-full">
      <div>
        <div className="flex items-center justify-between mb-3">
          <h2 className="font-bangers text-2xl tracking-wider">Examples</h2>
        </div>
        <div className="border-2 border-black border-b-4 border-r-4 rounded-xl p-4 bg-base-200">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
            {examples.map((example) => (
              <Link
                key={example.id}
                href={`/example/${example.id}`}
                className="relative overflow-visible card bg-base-200 hover:bg-base-300 border-2 border-black border-b-4 border-r-4 transform hover:translate-y-1 active:translate-y-2 transition-all group"
              >
                <div className="card-body p-4 relative">
                  <h3 className="font-vt323 text-xl text-base-content group-hover:text-warning tracking-wider transition-colors mb-3">
                    {example.name}
                  </h3>
                  <div className="flex items-center justify-between text-sm text-base-content/80">
                    <span className="flex items-center gap-1">
                      <BeakerIcon className="h-4 w-4 text-accent" />
                      Example
                    </span>
                    <span className="flex items-center gap-1 text-warning">
                      Try it
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
