/**
 * Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
 * SPDX-License-Identifier: SUL-1.0
 */

import { NodeEditorRepresentation } from "@/generated/editor";
import { useMemo, useState } from "react";
import { StatelessPad } from "./components/pads/StatelessPad";
import { FunnelIcon } from "@heroicons/react/24/outline";
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
        <div 
          className="flex w-full items-center justify-center gap-2 bg-base-300 border-b-2 border-black p-3 rounded-t-lg drag-handle cursor-pointer"
          onClick={() => setIsModalOpen(true)}
        >
          <FunnelIcon className="h-5 w-5 text-accent" />
          <div className="text-xs text-base-content/60 font-mono">
            {data.id}
          </div>
        </div>

        <div className="flex flex-1 flex-col gap-2 p-4 nodrag cursor-default">
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