/**
 * Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
 * SPDX-License-Identifier: SUL-1.0
 */

import { BaseEdge, Node, Position } from "@xyflow/react";
import { useEditor } from "../../../(providers)/useEditor";

const HANDLE_OFFSET = 20;
const BOTTOM_OFFSET = 80;

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
    let sourceBottomY = sourceY + BOTTOM_OFFSET;

    if (sourceNode && sourceNode.measured) {
      sourceBottomY = sourceNode.position.y + sourceNode.measured.height + 20;
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
