/**
 * Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
 * SPDX-License-Identifier: SUL-1.0
 */

import {
  NodeEditorRepresentation,
  PadEditorRepresentation,
} from "@/generated/editor";
import { useMemo, useState } from "react";
import { StatelessPad } from "./components/pads/StatelessPad";
import { FunnelIcon } from "@heroicons/react/24/outline";
import toast from "react-hot-toast";
import { StateTransitionModal } from "./components/modals/StateTransitionModal";

export interface StateTransitionNodeProps {
  data: NodeEditorRepresentation;
}

interface ParameterGroup {
  parameter?: PadEditorRepresentation;
  operator?: PadEditorRepresentation;
  value?: PadEditorRepresentation;
}

interface TypeConstraint {
  type: string;
}

export function StateTransitionNode({ data }: StateTransitionNodeProps) {
  const [isModalOpen, setIsModalOpen] = useState(false);

  // Get all entry pads (sinks) - these will be on the left
  const entryPads = useMemo(() => {
    // Find all entry pads
    return data.pads.filter((p) => p.id.startsWith("entry_"));
  }, [data]);

  // Get state pad (source) - this will be on the right
  const statePad = useMemo(() => {
    return data.pads.find((p) => p.id === "state");
  }, [data]);

  // Get parameter information
  const parameterInfo = useMemo(() => {
    const parameters = data.pads.filter(
      (p) =>
        p.id.startsWith("condition_parameter_") ||
        p.id.startsWith("condition_value_") ||
        p.id.startsWith("condition_operator_"),
    );

    // Group parameters by their index
    const groups = new Map<number, ParameterGroup>();
    parameters.forEach((p) => {
      const index = parseInt(p.id.split("_").pop() || "0");
      if (!groups.has(index)) {
        groups.set(index, {});
      }
      const group = groups.get(index)!;
      if (p.id.includes("parameter")) {
        group.parameter = p;
      } else if (p.id.includes("operator")) {
        group.operator = p;
      } else if (p.id.includes("value")) {
        group.value = p;
      }
    });

    // Convert to array and filter complete groups
    const allGroups = Array.from(groups.values());
    const paramGroups = allGroups.filter((g) => {
      if (!g.parameter) return false;
      
      // Check if it's a trigger parameter
      const typeConstraints = g.parameter.type_constraints as TypeConstraint[];
      
      // Handle trigger parameters
      if (typeConstraints?.some((c: TypeConstraint) => c.type === "Trigger")) {
        return true;
      }

      // For non-triggers, we need both operator and value
      return Boolean(g.operator && g.value);
    });

    // Create preview text
    const preview = paramGroups
      .map((g) => {
        const typeConstraints = g.parameter?.type_constraints as TypeConstraint[];
        if (typeConstraints?.some((c: TypeConstraint) => c.type === "Trigger")) {
          return `[Trigger] ${g.parameter?.value || "trigger"}`;
        }
        return `[Filter] ${g.parameter?.value || "param"} ${g.operator?.value || "="} ${
          g.value?.value || "?"
        }`;
      })
      .join("\n");

    return {
      count: paramGroups.length,
      preview,
    };
  }, [data.pads]);

  return (
    <>
      <div className="min-w-32 bg-base-200 border-2 border-black border-b-4 border-r-4 rounded-lg relative">
        {/* Left side - Entry pads (sinks) */}
        <div className="absolute left-0 top-1/2 -translate-y-1/2 -translate-x-1/2">
          <div className="flex flex-col gap-5">
            {entryPads.map((pad) => (
              <StatelessPad key={pad.id} data={pad} />
            ))}
          </div>
        </div>

        {/* Right side - State pad (source) */}
        {statePad && (
          <div className="absolute right-0 top-1/2 -translate-y-1/2 translate-x-1/2">
            <StatelessPad data={statePad} />
          </div>
        )}

        {/* Center - Title and icons */}
        <div className="px-3 py-2">
          <div className="text-center">
            <div
              className="text-sm font-medium text-primary cursor-pointer hover:text-primary/80"
              onClick={() => {
                navigator.clipboard.writeText(data.id);
                toast.success("ID copied to clipboard");
              }}
              title="Click to copy ID"
            >
              Transition
            </div>
            <button
              onClick={() => setIsModalOpen(true)}
              className="flex items-center gap-1.5 px-2 py-1 mt-1 text-xs hover:bg-base-300 rounded transition-colors group"
            >
              <span>Configure state transition</span>
              <FunnelIcon className="h-3.5 w-3.5 text-accent" />
              {/* Parameter preview tooltip */}
              <div className="absolute left-1/2 -translate-x-1/2 bottom-full mb-2 hidden group-hover:block">
                <div className="bg-base-300 text-left rounded-lg shadow-lg p-2 whitespace-pre text-xs">
                  <div className="font-medium mb-1">Parameters:</div>
                  {parameterInfo.preview || "No parameters"}
                </div>
                {/* Tooltip arrow */}
                <div className="absolute left-1/2 -translate-x-1/2 top-full -mt-2 border-8 border-transparent border-t-base-300" />
              </div>
            </button>
          </div>
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