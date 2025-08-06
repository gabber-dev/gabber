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

  // Get entry pad (sink) - this will be on the left
  const entryPad = useMemo(() => {
    // Find all sink pads for state connections
    const sinkPads = data.pads.filter(p => p.type === "StatelessSinkPad");
    // Find first unconnected pad or use the first pad
    return sinkPads.find(p => !p.previous_pad) || sinkPads[0];
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
    <div className="min-w-32 flex flex-col bg-base-200 border-2 border-black border-b-4 border-r-4 rounded-lg relative">
      <div className="relative px-3 pt-2 pb-1 flex items-center justify-between">
        {/* Left side - Entry pad (sink) */}
        <div className="nodrag cursor-default">
          {entryPad && <StatelessPad data={entryPad} forceVisible={true} />}
        </div>

        {/* Center - Node info */}
        <div className="flex-1 text-center">
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

        {/* Right side - Transition pad (source) */}
        <div className="nodrag cursor-default">
          {transitionPad && <StatelessPad data={transitionPad} />}
        </div>
      </div>
    </div>
  );
}