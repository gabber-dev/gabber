/**
 * Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
 * SPDX-License-Identifier: SUL-1.0
 */

import {
  BaseEdge,
  EdgeLabelRenderer,
  EdgeProps,
  getBezierPath,
  useInternalNode,
} from "@xyflow/react";
import { FunnelIcon } from "@heroicons/react/24/outline";
import { useStateMachine } from "./useStateMachine";
import { useEffect, useRef, useState } from "react";

// no-op: kept for potential future custom arrow needs

import { getEdgeParams } from "./floating";

export function StateMachineEdge({ id, source, target, style }: EdgeProps) {
  const { setEditingTransition } = useStateMachine();

  const sourceNode = useInternalNode(source);
  const targetNode = useInternalNode(target);
  if (!sourceNode || !targetNode) return null;

  const { sx, sy, tx, ty, sourcePos, targetPos } = getEdgeParams(
    sourceNode as any,
    targetNode as any,
  );

  const [edgePath, labelX, labelY] = getBezierPath({
    sourceX: sx,
    sourceY: sy,
    sourcePosition: sourcePos,
    targetX: tx,
    targetY: ty,
    targetPosition: targetPos,
  });

  // Entry edge should not have a filter icon
  const isEntryEdge = id === "entry_edge";

  const markerId = `sm-arrow-${id}`;

  const measurePathRef = useRef<SVGPathElement | null>(null);
  const [thirdPos, setThirdPos] = useState<{ x: number; y: number } | null>(
    null,
  );

  useEffect(() => {
    const p = measurePathRef.current;
    if (!p) return;
    try {
      const total = p.getTotalLength();
      const point = p.getPointAtLength(total * (1 / 3));
      setThirdPos({ x: point.x, y: point.y });
    } catch {
      // fallback gracefully; keep midpoint
      setThirdPos(null);
    }
  }, [edgePath]);

  return (
    <>
      <svg style={{ position: "absolute", width: 0, height: 0 }}>
        <defs>
          <marker
            id={markerId}
            viewBox="0 0 10 10"
            refX="9"
            refY="5"
            markerUnits="strokeWidth"
            markerWidth="3"
            markerHeight="3"
            orient="auto"
          >
            <path d="M 0 0 L 10 5 L 0 10 z" fill="#F59E0B" />
          </marker>
        </defs>
      </svg>
      <BaseEdge
        path={edgePath}
        style={{ stroke: "#F59E0B", strokeWidth: 2.5, ...(style || {}) }}
        markerEnd={`url(#${markerId})`}
      />
      {/* invisible path for measuring 1/3 position */}
      <path
        ref={measurePathRef}
        d={edgePath}
        stroke="transparent"
        fill="none"
        pointerEvents="none"
      />
      {!isEntryEdge && (
        <EdgeLabelRenderer>
          <div
            style={{
              position: "absolute",
              transform: `translate(-50%, -50%) translate(${thirdPos?.x ?? labelX}px, ${thirdPos?.y ?? labelY}px)`,
              pointerEvents: "all",
            }}
          >
            <button
              className="btn btn-ghost btn-xs bg-base-100 border border-base-300 shadow"
              title="Edit transition conditions"
              onClick={(e) => {
                e.stopPropagation();
                setEditingTransition?.(id);
              }}
            >
              <FunnelIcon className="w-4 h-4 text-base-content" />
            </button>
          </div>
        </EdgeLabelRenderer>
      )}
    </>
  );
}

export default StateMachineEdge;
