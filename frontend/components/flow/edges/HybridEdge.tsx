/**
 * Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
 * SPDX-License-Identifier: SUL-1.0
 */

import { getBezierPath, BaseEdge, EdgeProps, Position, Node } from "@xyflow/react";
import { getDataTypeColor } from "../blocks/components/pads/utils/dataTypeColors";
import { useEditor } from "@/hooks/useEditor";

const HANDLE_OFFSET = 20;
const BOTTOM_OFFSET = 80;
const CLEARANCE_OFFSET = 20;

export function HybridEdge({
  sourceX,
  sourceY,
  targetX,
  targetY,
  sourcePosition,
  targetPosition,
  source,
  target,
  style = {},
  markerEnd,
  data,
}: EdgeProps) {
  const { reactFlowRepresentation } = useEditor();
  // Determine if we should use step edge logic
  const isBackward = sourceX > targetX;
  const shouldUseStepEdge = isBackward;

  let edgePath: string;

  if (shouldUseStepEdge) {
    // Use step edge logic for backward connections
    const sourceExitX = sourceX + HANDLE_OFFSET;
    const targetApproachX =
      targetPosition === Position.Left
        ? targetX - HANDLE_OFFSET
        : targetX + HANDLE_OFFSET;
    // Compute clearance Y: 20px below the lower of the two nodes
    const sourceNode = reactFlowRepresentation.nodes.find(
      (n: Node) => n.id === source,
    );
    const targetNode = reactFlowRepresentation.nodes.find(
      (n: Node) => n.id === target,
    );

    let clearanceY = Math.max(sourceY, targetY) + BOTTOM_OFFSET; // fallback

    // Prefer live editor_dimensions from node data, fallback to measured
    const sourceHeight =
      (sourceNode?.data as any)?.editor_dimensions?.[1] ??
      (sourceNode?.measured?.height ?? null);
    const targetHeight =
      (targetNode?.data as any)?.editor_dimensions?.[1] ??
      (targetNode?.measured?.height ?? null);

    const measuredSourceBottom =
      sourceNode && sourceHeight ? sourceNode.position.y + sourceHeight : null;
    const measuredTargetBottom =
      targetNode && targetHeight ? targetNode.position.y + targetHeight : null;

    if (measuredSourceBottom !== null || measuredTargetBottom !== null) {
      const fallbackSource = measuredSourceBottom ?? sourceY;
      const fallbackTarget = measuredTargetBottom ?? targetY;
      const lowestBottom = Math.max(fallbackSource, fallbackTarget);
      clearanceY = lowestBottom + CLEARANCE_OFFSET;
    }

    edgePath = `M ${sourceX},${sourceY}
                L ${sourceExitX},${sourceY}
                L ${sourceExitX},${clearanceY}
                L ${targetApproachX},${clearanceY}
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

  const color = getDataTypeColor(
    typeof data?.dataType === "string" ? data.dataType : "default",
  );

  return (
    <BaseEdge
      path={edgePath}
      style={{ ...style, strokeWidth: 2, stroke: color.background }}
      markerEnd={markerEnd}
    />
  );
}
