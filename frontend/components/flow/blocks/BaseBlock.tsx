/**
 * Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
 * SPDX-License-Identifier: SUL-1.0
 */

import { NodeEditorRepresentation, PadEditorRepresentation } from "@/generated/editor";
import { useMemo, useState } from "react";
import { Handle, Position } from "@xyflow/react";
import { StatelessPad } from "./components/pads/StatelessPad";
import { PropertyPad } from "./components/pads/PropertyPad";
import { CubeIcon, ChevronUpIcon, ChevronDownIcon } from "@heroicons/react/24/outline";
import { Publish } from "./Publish";
import { Output } from "./Output";
import { AutoConvertNode } from "./AutoConvertNode";
import { CommentNode } from "./CommentNode";
import { SelfPad } from "./components/pads/SelfPad";
import { useMinimization } from "../FlowEdit";

export interface BaseBlockProps {
  data: NodeEditorRepresentation;
}

export function BaseBlock({ data }: BaseBlockProps) {
  const { minimizedNodes, toggleNodeMinimization } = useMinimization();
  const isMinimized = minimizedNodes.has(data.id);

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

  // Consolidated pads for minimized view
  const allSinkPads = useMemo(() => {
    return [...statelessSinkPad, ...propertySinkPad];
  }, [statelessSinkPad, propertySinkPad]);

  const allSourcePads = useMemo(() => {
    return [...statelessSourcePad, ...propertySourcePad];
  }, [statelessSourcePad, propertySourcePad]);

  if (data.type === "AutoConvert") {
    return <AutoConvertNode />;
  }

  if (data.type === "Comment") {
    return <CommentNode data={data} />;
  }

  return (
    <div className="min-w-64 flex flex-col bg-base-200 border-2 border-black border-b-4 border-r-4 rounded-lg relative">
      {/* Consolidated handles for minimized view - positioned relative to the node */}
      {isMinimized && allSinkPads.length > 0 && (
        <Handle
          type="target"
          position={Position.Left}
          id={`${data.id}-consolidated-sink`}
          style={{
            width: '16px',
            height: '16px',
            backgroundColor: '#FCD34D',
            border: '2px solid black',
            borderRadius: '50%',
            left: '0px',
            top: '50%',
            transform: 'translate(-50%, -50%)',
          }}
        />
      )}
      
      {isMinimized && allSourcePads.length > 0 && (
        <Handle
          type="source"
          position={Position.Right}
          id={`${data.id}-consolidated-source`}
          style={{
            width: '16px',
            height: '16px',
            backgroundColor: '#FCD34D',
            border: '2px solid black',
            borderRadius: '50%',
            right: '0px',
            top: '50%',
            transform: 'translate(50%, -50%)',
          }}
        />
      )}

      <div className="flex w-full items-center gap-2 bg-base-300 border-b-2 border-black p-3 rounded-t-lg drag-handle cursor-grab active:cursor-grabbing">
        {/* Consolidated pad tooltip areas for minimized view */}
        {isMinimized && allSinkPads.length > 0 && (
          <div className="absolute left-0 top-1/2 transform -translate-y-1/2 -translate-x-1/2">
            <ConsolidatedPadTooltip pads={allSinkPads} type="sink" />
          </div>
        )}
        
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
          onClick={(e) => {
            e.stopPropagation();
            toggleNodeMinimization(data.id);
          }}
          className="p-1 hover:bg-base-100 rounded transition-colors nodrag"
        >
          {isMinimized ? (
            <ChevronDownIcon className="h-4 w-4 text-base-content" />
          ) : (
            <ChevronUpIcon className="h-4 w-4 text-base-content" />
          )}
        </button>

        {/* Self pad and right side consolidated source pad for minimized view */}
        <div className="absolute right-0 flex items-center">
          {selfPad && <SelfPad data={selfPad} nodeId={data.id} />}
          {isMinimized && allSourcePads.length > 0 && (
            <div className="absolute right-0 top-1/2 transform -translate-y-1/2 translate-x-1/2">
              <ConsolidatedPadTooltip pads={allSourcePads} type="source" />
            </div>
          )}
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

// Consolidated pad tooltip component for minimized view
interface ConsolidatedPadTooltipProps {
  pads: PadEditorRepresentation[];
  type: "source" | "sink";
}

function ConsolidatedPadTooltip({ pads, type }: ConsolidatedPadTooltipProps) {
  const [showTooltip, setShowTooltip] = useState(false);

  if (pads.length === 0) return null;

  return (
    <div
      className="relative w-4 h-4 flex items-center justify-center cursor-pointer"
      onMouseEnter={() => setShowTooltip(true)}
      onMouseLeave={() => setShowTooltip(false)}
    >
      {/* Visual indicator */}
      <div className="w-2 h-2 bg-black rounded-full"></div>

      {/* Tooltip showing individual pads */}
      {showTooltip && (
        <div className={`absolute z-50 bg-base-300 border-2 border-black rounded-lg p-2 shadow-lg min-w-48 ${
          type === "source" ? "right-0 top-6" : "left-0 top-6"
        }`}>
          <div className="text-xs font-bold mb-2 text-base-content">
            {type === "source" ? "Source Pads" : "Sink Pads"} ({pads.length})
          </div>
          <div className="space-y-1">
            {pads.map((pad) => {
              const isConnected = type === "source" 
                ? (pad.next_pads && pad.next_pads.length > 0)
                : (pad.previous_pad !== null);
              
              return (
                <div key={pad.id} className="flex items-center justify-between text-xs">
                  <span className="text-base-content truncate mr-2">
                    {pad.display_name || pad.id}
                  </span>
                  <span className={`w-2 h-2 rounded-full ${
                    isConnected ? "bg-success" : "bg-error"
                  }`} title={isConnected ? "Connected" : "Not connected"}>
                  </span>
                </div>
              );
            })}
          </div>
        </div>
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
