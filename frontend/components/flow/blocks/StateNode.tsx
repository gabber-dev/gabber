/**
 * Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
 * SPDX-License-Identifier: SUL-1.0
 */

import { NodeEditorRepresentation } from "@/generated/editor";
import { StatelessPad } from "./components/pads/StatelessPad";
import { useMemo, useState, useCallback } from "react";
import { useEditor } from "@/hooks/useEditor";
import toast from "react-hot-toast";

export interface StateNodeProps {
  data: NodeEditorRepresentation;
}

export function StateNode({ data }: StateNodeProps) {
  const editor = useEditor();
  const [isEditing, setIsEditing] = useState(false);

  // Get the name value from the name pad
  const namePad = useMemo(() => {
    return data.pads.find((p) => p.id === "name" && p.type === "PropertySinkPad");
  }, [data]);

  // Get all entry pads (sinks) - these will be on the left
  const entryPads = useMemo(() => {
    // Find all sink pads for state connections
    return data.pads.filter(p => p.type === "StatelessSinkPad");
  }, [data]);

  // Find transition pad (source) - this will be on the right
  const transitionPad = useMemo(() => {
    // Use the transition pad for outgoing connections
    return data.pads.find((p) => p.id === "transition" && p.type === "StatelessSourcePad");
  }, [data]);

  const handleNameChange = useCallback((newName: string) => {
    if (namePad) {
      editor.updatePad({
        type: "update_pad",
        node: data.id,
        pad: namePad.id,
        value: newName
      });
    }
  }, [editor, data.id, namePad]);

  const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      setIsEditing(false);
    }
  }, []);

  return (
    <div className="min-w-32 bg-base-200 border-2 border-black border-b-4 border-r-4 rounded-lg relative">
      {/* Left side - Entry pads (sinks) */}
      <div className="absolute left-0 top-1/2 -translate-y-1/2 -translate-x-1/2">
        <div className="flex flex-col gap-5">
          {entryPads.map((pad) => (
            <StatelessPad key={pad.id} data={pad} />
          ))}
        </div>
      </div>

      {/* Right side - Transition pad (source) */}
      {transitionPad && (
        <div className="absolute right-0 top-1/2 -translate-y-1/2 translate-x-1/2">
          <StatelessPad data={transitionPad} />
        </div>
      )}

      {/* Center - Node info */}
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
            State
          </div>
          {isEditing ? (
            <input
              type="text"
              className="w-full text-sm bg-transparent border-b border-accent/50 focus:border-accent outline-none text-center"
              value={namePad?.value || ""}
              onChange={(e) => handleNameChange(e.target.value)}
              onBlur={() => setIsEditing(false)}
              onKeyDown={handleKeyDown}
              autoFocus
            />
          ) : (
            <div 
              className="text-sm text-base-content/80 cursor-text"
              onClick={() => setIsEditing(true)}
            >
              {namePad?.value || "Unnamed State"}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}