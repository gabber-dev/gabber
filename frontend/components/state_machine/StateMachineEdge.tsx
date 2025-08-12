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

export function StateMachineEdge(props: EdgeProps) {
  const {
    id,
    source,
    target,
    style,
    sourceX,
    sourceY,
    targetX,
    targetY,
    sourcePosition,
    targetPosition,
    selected,
  } = props;
  const { setEditingTransition, reactFlowRepresentation } = useStateMachine();

  const sourceNode = useInternalNode(source);
  const targetNode = useInternalNode(target);

  let edgePath = "";
  let labelX = 0; // kept for potential future label features
  let labelY = 0;
  if (sourceNode && targetNode) {
    const { sx, sy, tx, ty } = getEdgeParams(
      sourceNode as unknown as {
        measured: { width: number; height: number };
        internals: { positionAbsolute: { x: number; y: number } };
      },
      targetNode as unknown as {
        measured: { width: number; height: number };
        internals: { positionAbsolute: { x: number; y: number } };
      },
    );
    // determine how many edges connect this pair (both directions)
    const pairKey = ([a, b]: [string, string]) =>
      a < b ? `${a}|${b}` : `${b}|${a}`;
    const currentPair = pairKey([source, target]);
    const pairEdges = (reactFlowRepresentation?.edges || []).filter(
      (e) => pairKey([e.source as string, e.target as string]) === currentPair,
    );
    const directionThenId = (
      a: { id?: string; source: string; target: string },
      b: { id?: string; source: string; target: string },
    ) => {
      const aForward = a.source < a.target;
      const bForward = b.source < b.target;
      if (aForward !== bForward) return aForward ? -1 : 1;
      return (a.id || "").localeCompare(b.id || "");
    };
    const sortedPairEdges = [...pairEdges].sort(directionThenId);
    const pairIndex = sortedPairEdges.findIndex((e) => e.id === id);
    const pairCount = sortedPairEdges.length || 1;

    // offset along the normal to reduce overlap
    // visual tuning
    const SEPARATION_STEP = 22; // distance between neighboring curves
    const CURVE_FACTOR = 0.6; // how bowed the curves are (0..1)
    // actual path vector
    const dx = tx - sx;
    const dy = ty - sy;
    // canonical vector (consistent for both directions)
    const canonicalFromIsSource = (source as string) < (target as string);
    const ax = canonicalFromIsSource ? sx : tx;
    const ay = canonicalFromIsSource ? sy : ty;
    const bx = canonicalFromIsSource ? tx : sx;
    const by = canonicalFromIsSource ? ty : sy;
    const cdx = bx - ax;
    const cdy = by - ay;
    const clen = Math.max(1, Math.hypot(cdx, cdy));
    const nx = -cdy / clen;
    const ny = cdx / clen;
    // symmetric distribution; for even counts use half-step to avoid stacking near center
    const unitIndex = pairIndex - (pairCount - 1) / 2;
    const evenHalfStep = pairCount % 2 === 0 ? 0.5 : 0;
    const adjustedIndex =
      unitIndex + (unitIndex >= 0 ? evenHalfStep : -evenHalfStep);
    const offset = adjustedIndex * SEPARATION_STEP;

    // control points along the line, pushed out by the offset normal
    const t1 = 0.2;
    const t2 = 0.8;
    const offsetForCurve = offset * CURVE_FACTOR;
    const c1x = sx + dx * t1 + nx * offsetForCurve;
    const c1y = sy + dy * t1 + ny * offsetForCurve;
    const c2x = sx + dx * t2 + nx * offsetForCurve;
    const c2y = sy + dy * t2 + ny * offsetForCurve;

    // Straight-line rule:
    // - when exactly 2 edges exist, make the later-sorted one straight (pairIndex === 1)
    // - when odd counts (>=3), middle edge straight (unitIndex === 0)
    const makeStraight =
      (pairCount === 2 && pairIndex === 1) ||
      (pairCount >= 3 && pairCount % 2 === 1 && Math.abs(unitIndex) < 1e-6);

    if (makeStraight) {
      edgePath = `M ${sx},${sy} L ${tx},${ty}`;
      labelX = (sx + tx) / 2;
      labelY = (sy + ty) / 2;
    } else {
      edgePath = `M ${sx},${sy} C ${c1x},${c1y} ${c2x},${c2y} ${tx},${ty}`;
      // fallback midpoint for label; precise 1/3 will be measured via ref
      labelX = sx + dx * 0.5 + nx * offsetForCurve * 0.25;
      labelY = sy + dy * 0.5 + ny * offsetForCurve * 0.25;
    }
  } else {
    // Fallback during transient re-measure/re-render while dragging
    [edgePath, labelX, labelY] = getBezierPath({
      sourceX: sourceX!,
      sourceY: sourceY!,
      sourcePosition: sourcePosition!,
      targetX: targetX!,
      targetY: targetY!,
      targetPosition: targetPosition!,
    });
  }

  // Entry edge should not have a filter icon
  const isEntryEdge = id === "entry_edge";

  const measurePathRef = useRef<SVGPathElement | null>(null);
  // We compute midPos for arrow/filter placement
  const [thirdPos, setThirdPos] = useState<{ x: number; y: number } | null>(
    null,
  );
  const [midPos, setMidPos] = useState<{ x: number; y: number } | null>(null);
  const [midAngle, setMidAngle] = useState<number>(0);
  const [isHovered, setIsHovered] = useState<boolean>(false);

  useEffect(() => {
    const p = measurePathRef.current;
    if (!p) return;
    try {
      const total = p.getTotalLength();
      const point = p.getPointAtLength(total * (1 / 3));
      setThirdPos({ x: point.x, y: point.y });
      const mid = p.getPointAtLength(total * 0.5);
      const ahead = p.getPointAtLength(Math.min(total, total * 0.5 + 1));
      setMidPos({ x: mid.x, y: mid.y });
      const angle = Math.atan2(ahead.y - mid.y, ahead.x - mid.x);
      setMidAngle(angle);
    } catch {
      // fallback gracefully; keep midpoint
      setThirdPos(null);
      setMidPos(null);
    }
  }, [edgePath]);

  return (
    <>
      <BaseEdge
        path={edgePath}
        style={{
          stroke: selected ? "#FFFFFF" : "#F59E0B",
          strokeWidth: 2.5,
          ...(style || {}),
        }}
      />
      {/* interactive overlay for hover/click, with generous hit area */}
      <path
        d={edgePath}
        fill="none"
        stroke="transparent"
        strokeWidth={16}
        pointerEvents="stroke"
        onMouseEnter={() => setIsHovered(true)}
        onMouseLeave={() => setIsHovered(false)}
        onClick={(e) => {
          e.stopPropagation();
          if (id !== "entry_edge") setEditingTransition?.(id);
        }}
      />
      {/* invisible path for measuring 1/3 position */}
      <path
        ref={measurePathRef}
        d={edgePath}
        stroke="transparent"
        fill="none"
        pointerEvents="none"
      />
      {/* Show arrow by default; on hover, show filter icon in its place */}
      {!isEntryEdge && midPos && !isHovered && (
        <EdgeLabelRenderer>
          <svg
            style={{
              position: "absolute",
              overflow: "visible",
              transform: `translate(${midPos.x}px, ${midPos.y}px)`,
            }}
          >
            <g transform={`rotate(${(midAngle * 180) / Math.PI})`}>
              <polygon
                points="0,0 -6,-3 -6,3"
                fill={selected ? "#FFFFFF" : "#F59E0B"}
              />
            </g>
          </svg>
        </EdgeLabelRenderer>
      )}
      {!isEntryEdge && midPos && isHovered && (
        <EdgeLabelRenderer>
          <div
            style={{
              position: "absolute",
              transform: `translate(-50%, -50%) translate(${midPos.x}px, ${midPos.y}px)`,
              pointerEvents: "all",
            }}
            onMouseEnter={() => setIsHovered(true)}
            onMouseLeave={() => setIsHovered(false)}
          >
            <div
              title="Edit transition conditions"
              onClick={(e) => {
                e.stopPropagation();
                setEditingTransition?.(id);
              }}
              className="bg-base-100 border border-base-300 shadow rounded"
              style={{ padding: 1, lineHeight: 0, cursor: "pointer" }}
            >
              <FunnelIcon className="w-2 h-2 text-base-content" />
            </div>
          </div>
        </EdgeLabelRenderer>
      )}
    </>
  );
}

export default StateMachineEdge;

