/**
 * Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
 * SPDX-License-Identifier: SUL-1.0
 */

import { getBezierPath, BaseEdge, EdgeProps, Position } from "@xyflow/react";

const HANDLE_OFFSET = 20;
const BOTTOM_OFFSET = 80;

export function HybridEdge({
  id,
  sourceX,
  sourceY,
  targetX,
  targetY,
  sourcePosition,
  targetPosition,
  source,
  style = {},
  markerEnd,
}: EdgeProps) {
  // Determine if we should use step edge logic
  const isBackward = sourceX > targetX;
  const isSourceRight = sourcePosition === Position.Right;
  const shouldUseStepEdge = isBackward && isSourceRight;

  let edgePath: string;

  if (shouldUseStepEdge) {
    // Use step edge logic for backward connections
    const sourceExitX = sourceX + HANDLE_OFFSET;
    const targetApproachX =
      targetPosition === Position.Left
        ? targetX - HANDLE_OFFSET
        : targetX + HANDLE_OFFSET;

    const sourceBottomY = sourceY + BOTTOM_OFFSET;

    edgePath = `M ${sourceX},${sourceY}
                L ${sourceExitX},${sourceY}
                L ${sourceExitX},${sourceBottomY}
                L ${targetApproachX},${sourceBottomY}
                L ${targetApproachX},${targetY}
                L ${targetX},${targetY}`;
  } else {
    // Use bezier edge logic for forward connections
    [edgePath] = getBezierPath({
      sourceX,
      sourceY,
      sourcePosition,
      targetX,
      targetY,
      targetPosition,
    });
  }

  return (
    <BaseEdge
      path={edgePath}
      style={{ ...style, strokeWidth: 2, stroke: "#FCD34D" }}
      markerEnd={markerEnd}
    />
  );
}
