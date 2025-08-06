/**
 * Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
 * SPDX-License-Identifier: SUL-1.0
 */

import { BaseEdge, Node, Position } from "@xyflow/react";
import { useEditor } from "@/hooks/useEditor";

const HANDLE_OFFSET = 20;
const BOTTOM_PADDING = 20;

export function CustomStepEdge({
  sourceX,
  sourceY,
  targetX,
  targetY,
  sourcePosition,
  targetPosition,
  source,
  style = {},
  markerEnd,
}: any) {
  const { reactFlowRepresentation } = useEditor();

  const isBackward = sourceX > targetX;
  const isSourceRight = sourcePosition === Position.Right;
  const isTargetLeft = targetPosition === Position.Left;

  const sourceExitX = isSourceRight
    ? sourceX + HANDLE_OFFSET
    : sourceX - HANDLE_OFFSET;
  const targetApproachX = isTargetLeft
    ? targetX - HANDLE_OFFSET
    : targetX + HANDLE_OFFSET;

  let edgePath: string;
  if (isBackward && isSourceRight) {
    const sourceNode = reactFlowRepresentation.nodes.find(
      (n: Node) => n.id === source,
    );
    // Default to using the source node's Y position plus its height from the DOM
    const sourceNodeElement = document.querySelector(`[data-id="${source}"]`);
    let sourceBottomY = sourceY;

    if (sourceNode && sourceNode.measured) {
      // Use the measured height if available
      sourceBottomY = sourceNode.position.y + sourceNode.measured.height + BOTTOM_PADDING;
    } else if (sourceNodeElement) {
      // Fallback to DOM measurement
      sourceBottomY = sourceY + sourceNodeElement.getBoundingClientRect().height + BOTTOM_PADDING;
    } else {
      // Last resort - use source Y plus a reasonable default
      sourceBottomY = sourceY + 120 + BOTTOM_PADDING;
    }

    edgePath = `M ${sourceX},${sourceY}
                L ${sourceExitX},${sourceY}
                L ${sourceExitX},${sourceBottomY}
                L ${targetApproachX},${sourceBottomY}
                L ${targetApproachX},${targetY}
                L ${targetX},${targetY}`;
  } else {
    edgePath = `M ${sourceX},${sourceY}
                L ${sourceExitX},${sourceY}
                L ${sourceExitX},${targetY}
                L ${targetApproachX},${targetY}
                L ${targetX},${targetY}`;
  }

  return (
    <BaseEdge
      path={edgePath}
      markerEnd={markerEnd}
      style={{ ...style, strokeWidth: 2, stroke: "#FCD34D" }}
    />
  );
}
