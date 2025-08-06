/**
 * Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
 * SPDX-License-Identifier: SUL-1.0
 */

import { NodeEditorRepresentation } from "@/generated/editor";
import { useMemo, useState } from "react";
import { StatelessPad } from "./components/pads/StatelessPad";
import { Cog6ToothIcon } from "@heroicons/react/24/outline";
import { StateTransitionModal } from "./components/modals/StateTransitionModal";

export interface StateTransitionNodeProps {
  data: NodeEditorRepresentation;
}

export function StateTransitionNode({ data }: StateTransitionNodeProps) {
  const [isModalOpen, setIsModalOpen] = useState(false);

  // Only show entry and state pads in the node
  const pads = useMemo(() => {
    return data.pads.filter(
      (p) => p.id === "entry_0" || p.id === "entry_1" || p.id === "state",
    );
  }, [data]);

  return (
    <>
      <div className="min-w-32 flex flex-col bg-base-200 border-2 border-black border-b-4 border-r-4 rounded-lg relative">
        <div className="relative px-3 pt-2 pb-1">
          <button 
            onClick={() => setIsModalOpen(true)}
            className="absolute top-1.5 right-2 p-1 hover:bg-base-300 rounded transition-colors"
          >
            <Cog6ToothIcon className="h-4 w-4 text-accent" />
          </button>
          
          <div className="text-sm font-medium text-primary">State Transition</div>
          <div className="text-[10px] font-mono text-base-content/60 -mt-0.5">{data.id}</div>
        </div>

        <div className="flex flex-1 flex-col gap-1.5 p-2 nodrag cursor-default">
          {pads.map((pad) => (
            <div key={pad.id}>
              <StatelessPad data={pad} />
            </div>
          ))}
        </div>
      </div>

      <StateTransitionModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        nodeData={data}
      />
    </>
  );
}