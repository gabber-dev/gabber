/**
 * Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
 * SPDX-License-Identifier: SUL-1.0
 */

import { useRepository } from "@/hooks/useRepository";

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
              <div key={example.id}>{example.name}</div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
