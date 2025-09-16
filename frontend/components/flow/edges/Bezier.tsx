/**
 * Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
 * SPDX-License-Identifier: SUL-1.0
 */

import {
  BaseEdge,
  EdgeLabelRenderer,
  getSmoothStepPath,
  EdgeProps,
} from "@xyflow/react";

export function BasicBezierEdge({
  sourceX,
  sourceY,
  targetX,
  targetY,
  sourcePosition,
  targetPosition,
  data,
}: EdgeProps) {
  const [edgePath, labelX, labelY] = getSmoothStepPath({
    sourceX,
    sourceY,
    sourcePosition,
    targetX,
    targetY,
    targetPosition,
  });

  const dataLabel = (data as { label: string | undefined }).label || "Edge";

  return (
    <>
      <BaseEdge
        path={edgePath}
        style={{ stroke: "#333", strokeWidth: 2 }}
        markerEnd="url(#arrow)"
      />
      <EdgeLabelRenderer>
        <div
          style={{
            position: "absolute",
            transform: `translate(-50%, -50%) translate(${labelX}px,${labelY}px)`,
            background: "#fff",
            padding: "2px 5px",
            borderRadius: 3,
            fontSize: 12,
            border: "1px solid #333",
          }}
        >
          {dataLabel}
        </div>
      </EdgeLabelRenderer>
    </>
  );
}
