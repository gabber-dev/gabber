/**
 * Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
 * SPDX-License-Identifier: SUL-1.0
 */

import { BaseBlockProps } from "./BaseBlock";
import { usePropertyPad } from "./components/pads/hooks/usePropertyPad";
import { CubeIcon } from "@heroicons/react/24/outline";
import { NodeName } from "./components/NodeName";
import { NodeId } from "./components/NodeId";
import { PropertyPad } from "./components/pads/PropertyPad";
import { StatelessPad } from "./components/pads/StatelessPad";
import { SelfPad } from "./components/pads/SelfPad";
import { useMemo } from "react";
import { PadValue, PadValue_List } from "@gabber/client-react";
import { useEditor } from "@/hooks/useEditor";

export function LLMContextNode({ data }: BaseBlockProps) {
  const { detailedView, setDetailedView } = useEditor();
  const propertyPadResult = usePropertyPad<PadValue_List | PadValue[]>(
    data.id,
    "source",
  );
  const { runtimeValue: contextMessages, editorValue } = propertyPadResult;

  const sinkPads = useMemo(() => {
    return data.pads.filter(
      (p) => p.type === "StatelessSinkPad" || p.type === "PropertySinkPad",
    );
  }, [data]);

  const sourcePads = useMemo(() => {
    return data.pads.filter(
      (p) =>
        p.type === "StatelessSourcePad" ||
        (p.type === "PropertySourcePad" && p.id !== "self"),
    );
  }, [data]);

  const selfPad = useMemo(() => {
    return data.pads.find(
      (p) => p.type === "PropertySourcePad" && p.id === "self",
    );
  }, [data]);

  // Use contextMessages from runtime, fallback to editorValue
  const messages = useMemo(() => {
    const msgs = contextMessages || editorValue || [];
    // Ensure it's an array
    const result = Array.isArray(msgs) ? msgs : [];
    return result;
  }, [contextMessages, editorValue]);

  const messageCount = messages.length;

  return (
    <div className="w-80 flex flex-col bg-base-200 border-2 border-black border-b-4 border-r-4 rounded-lg relative">
      <div className="flex w-full items-center gap-2 bg-base-300 border-b-2 border-black p-3 rounded-t-lg drag-handle cursor-grab active:cursor-grabbing">
        <CubeIcon className="h-5 w-5 text-accent" />
        <div className="flex-1 min-w-0">
          <NodeName />
          <NodeId />
        </div>

        <div className="absolute right-0">
          {selfPad && <SelfPad data={selfPad} nodeId={data.id} />}
        </div>
      </div>

      {/* Context Messages Viewer */}
      <div className="flex flex-col gap-1 p-1">
        <button
          className="btn btn-sm btn-ghost gap-1"
          onClick={() =>
            setDetailedView({
              nodeId: data.id,
              padId: "source",
              type: "property",
            })
          }
        >
          Inspect ({messageCount}) Items
        </button>
      </div>

      <div className="flex flex-1 flex-col gap-2 p-4 nodrag cursor-default">
        {sourcePads.map((pad) => {
          if (pad.type === "StatelessSourcePad") {
            return (
              <div key={pad.id}>
                <StatelessPad
                  data={pad}
                  notes={(data.notes || []).filter(
                    (note) => note.pad === pad.id,
                  )}
                />
              </div>
            );
          } else if (pad.type === "PropertySourcePad") {
            return (
              <div key={pad.id}>
                <PropertyPad
                  nodeId={data.id}
                  data={pad}
                  notes={(data.notes || []).filter(
                    (note) => note.pad === pad.id,
                  )}
                />
              </div>
            );
          }
        })}
        {sinkPads.map((pad) => {
          if (pad.type === "StatelessSinkPad") {
            return (
              <div key={pad.id}>
                <StatelessPad
                  data={pad}
                  notes={(data.notes || []).filter(
                    (note) => note.pad === pad.id,
                  )}
                />
              </div>
            );
          } else if (pad.type === "PropertySinkPad") {
            return (
              <div key={pad.id}>
                <PropertyPad
                  nodeId={data.id}
                  data={pad}
                  notes={(data.notes || []).filter(
                    (note) => note.pad === pad.id,
                  )}
                />
              </div>
            );
          }
        })}
      </div>
    </div>
  );
}
