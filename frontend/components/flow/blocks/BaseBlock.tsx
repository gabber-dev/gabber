/**
 * Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
 * SPDX-License-Identifier: SUL-1.0
 */

import { NodeEditorRepresentation } from "@/generated/editor";
import { useMemo } from "react";
import { StatelessPad } from "./components/pads/StatelessPad";
import { PropertyPad } from "./components/pads/PropertyPad";
import {
  CubeIcon,
  ChevronUpIcon,
  ChevronDownIcon,
} from "@heroicons/react/24/outline";
import { Publish } from "./Publish";
import { Output } from "./Output";
import { AutoConvertNode } from "./AutoConvertNode";
import { CommentNode } from "./CommentNode";
import { SelfPad } from "./components/pads/SelfPad";
import { Handle, Position } from "@xyflow/react";
import { useEditor } from "@/hooks/useEditor";

export interface BaseBlockProps {
  data: NodeEditorRepresentation;
}

export function BaseBlock({ data }: BaseBlockProps) {
  const { toggleDisplayState } = useEditor();

  // Backend will provide display_state when types are updated
  const isMinimized = (data as any).display_state === "minimized";

  const toggleNodeMinimization = () => {
    toggleDisplayState(data.id);
  };

  const statelessSinkPad = useMemo(() => {
    return data.pads.filter((p) => p.type === "StatelessSinkPad");
  }, [data]);
  const statelessSourcePad = useMemo(() => {
    return data.pads.filter((p) => p.type === "StatelessSourcePad");
  }, [data]);

  const propertySinkPad = useMemo(() => {
    return data.pads.filter((p) => p.type === "PropertySinkPad");
  }, [data]);

  const propertySourcePad = useMemo(() => {
    return data.pads.filter(
      (p) => p.type === "PropertySourcePad" && p.id !== "self",
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

  // Add ambient-float by default, but remove it if selected
  // React Flow adds .selected to the node when selected
  // We'll use a className that is always present, and CSS will handle the rest
  return (
    <div className="min-w-64 flex flex-col bg-base-200 border-2 border-black border-b-4 border-r-4 rounded-lg relative">
      {/* Consolidated handles for minimized view - backend provides these */}
      {isMinimized &&
        (data as any).consolidated_pads?.map((consolPad: any) => (
          <div
            key={consolPad.id}
            className={`absolute top-1/2 transform -translate-y-1/2 ${
              consolPad.type === "sink"
                ? "left-0 -translate-x-1/2"
                : "right-0 translate-x-1/2"
            }`}
          >
            <ConsolidatedPadTooltip pad={consolPad} />
            <Handle
              type={consolPad.type === "sink" ? "target" : "source"}
              position={
                consolPad.type === "sink" ? Position.Left : Position.Right
              }
              id={consolPad.id}
              style={{
                width: "16px",
                height: "16px",
                backgroundColor: "#FCD34D",
                border: "2px solid black",
                borderRadius: "50%",
              }}
            />
          </div>
        ))}

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
        {/* Minimize/Expand button */}
        <button
          onClick={toggleNodeMinimization}
          className="p-1 hover:bg-base-100 rounded nodrag"
          title={isMinimized ? "Expand node" : "Minimize node"}
        >
          {isMinimized ? (
            <ChevronDownIcon className="h-4 w-4" />
          ) : (
            <ChevronUpIcon className="h-4 w-4" />
          )}
        </button>

        <div className="absolute right-0">
          {selfPad && <SelfPad data={selfPad} nodeId={data.id} />}
        </div>
      </div>

      {!isMinimized && (
        <>
          <div className="">
            <Inner data={data} />
          </div>

          <div className="flex flex-1 flex-col gap-3 p-4 nodrag cursor-default">
            {statelessSourcePad.map((pad) => {
              return (
                <div key={pad.id}>
                  <StatelessPad data={pad} />
                </div>
              );
            })}
            {propertySourcePad.map((pad) => {
              return (
                <div key={pad.id}>
                  <PropertyPad nodeId={data.id} data={pad} />
                </div>
              );
            })}
            {statelessSinkPad.map((pad) => {
              return (
                <div key={pad.id}>
                  <StatelessPad data={pad} />
                </div>
              );
            })}
            {propertySinkPad.map((pad) => {
              return (
                <div key={pad.id}>
                  <PropertyPad nodeId={data.id} data={pad} />
                </div>
              );
            })}
          </div>
        </>
      )}
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

interface ConsolidatedPadTooltipProps {
  pad: {
    id: string;
    type: "sink" | "source";
    represented_pads: string[];
  };
}

function ConsolidatedPadTooltip({ pad }: ConsolidatedPadTooltipProps) {
  return (
    <div
      className="tooltip tooltip-right"
      data-tip={`${pad.type === "sink" ? "Inputs" : "Outputs"}: ${pad.represented_pads.join(", ")}`}
    >
      <div className="w-4 h-4" />
    </div>
  );
}
