/**
 * Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
 * SPDX-License-Identifier: SUL-1.0
 */

import { NodeEditorRepresentation } from "@/generated/editor";
import { useMemo } from "react";
import { StatelessPad } from "./components/pads/StatelessPad";
import { PropertyPad } from "./components/pads/PropertyPad";
import { CubeIcon } from "@heroicons/react/24/outline";
import { Publish } from "./Publish";
import { Output } from "./Output";
import { AutoConvertNode } from "./AutoConvertNode";
import { CommentNode } from "./CommentNode";
import { StateTransitionNode } from "./StateTransitionNode";
import { SelfPad } from "./components/pads/SelfPad";
import { StateMachineNode } from "@/components/state_machine/StateMachineNode";

export interface BaseBlockProps {
  data: NodeEditorRepresentation;
}

export function BaseBlock({ data }: BaseBlockProps) {
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
    return data.pads.filter(
      (p) => p.type === "PropertySourcePad" && p.id === "self",
    )[0];
  }, [data]);

  if (data.type === "AutoConvert") {
    return <AutoConvertNode />;
  }

  if (data.type === "Comment") {
    return <CommentNode data={data} />;
  }

  if (data.type === "StateMachine") {
    return <StateMachineNode data={data} />;
  }

  // Add ambient-float by default, but remove it if selected
  // React Flow adds .selected to the node when selected
  // We'll use a className that is always present, and CSS will handle the rest
  return (
    <div className="min-w-64 flex flex-col bg-base-200 border-2 border-black border-b-4 border-r-4 rounded-lg relative">
      <div className="flex w-full items-center gap-2 bg-base-300 border-b-2 border-black p-3 rounded-t-lg drag-handle cursor-grab active:cursor-grabbing">
        <CubeIcon className="h-5 w-5 text-accent" />
        <div className="flex-1">
          <h2 className="text-lg text-primary font-medium">
            {data.editor_name}
          </h2>
          <div className="text-xs text-base-content/60 font-mono">
            {data.id}
          </div>
        </div>
        <div className="absolute right-0">
          {selfPad && <SelfPad data={selfPad} nodeId={data.id} />}
        </div>
      </div>

      <div className="">
        <Inner data={data} />
      </div>

      <div className="flex flex-1 flex-col gap-2 p-4 nodrag cursor-default">
        {sourcePads.map((pad) => {
          if (pad.type === "StatelessSourcePad") {
            return (
              <div key={pad.id}>
                <StatelessPad data={pad} />
              </div>
            );
          } else if (pad.type === "PropertySourcePad") {
            return (
              <div key={pad.id}>
                <PropertyPad nodeId={data.id} data={pad} />
              </div>
            );
          }
        })}
        {sinkPads.map((pad) => {
          if (pad.type === "StatelessSinkPad") {
            return (
              <div key={pad.id}>
                <StatelessPad data={pad} />
              </div>
            );
          } else if (pad.type === "PropertySinkPad") {
            return (
              <div key={pad.id}>
                <PropertyPad nodeId={data.id} data={pad} />
              </div>
            );
          }
        })}
      </div>
    </div>
  );
}

function Inner({ data }: BaseBlockProps) {
  if (data.type === "Publish") {
    return <Publish />;
  } else if (data.type === "Output") {
    return <Output />;
  }
  return null;
}
