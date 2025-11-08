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
import { List, PadValue, usePad } from "@gabber/client-react";
import { useEditor } from "@/hooks/useEditor";
import { useRun } from "@/hooks/useRun";
import { useStatelessPad } from "./components/pads/hooks/useStatelessPad";
import { Viseme } from "@/generated/editor";

export function VisemeDebugNode({ data }: BaseBlockProps) {
  const { lastValue } = usePad<Viseme>(data.id, "viseme");

  const sinkPads = useMemo(() => {
    return data.pads.filter(
      (p) => p.type === "StatelessSinkPad" || p.type === "PropertySinkPad",
    );
  }, [data]);

  return (
    <div className="w-80 flex flex-col bg-base-200 border-2 border-black border-b-4 border-r-4 rounded-lg relative">
      <div className="flex w-full items-center gap-2 bg-base-300 border-b-2 border-black p-3 rounded-t-lg drag-handle cursor-grab active:cursor-grabbing">
        <CubeIcon className="h-5 w-5 text-accent" />
        <div className="flex-1 min-w-0">
          <NodeName />
          <NodeId />
        </div>
      </div>

      <div>{lastValue?.value as string}</div>

      <div className="flex flex-1 flex-col gap-2 p-4 nodrag cursor-default">
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
