/**
 * Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
 * SPDX-License-Identifier: SUL-1.0
 */

import { BaseEdge, EdgeProps, Node, Position } from "@xyflow/react";
import { useEditor } from "@/hooks/useEditor";
import { NodeEditorRepresentation } from "@/generated/editor";

const HANDLE_OFFSET = 20;
const BOTTOM_OFFSET = 80;
const CLEARANCE_OFFSET = 20;

export function CustomStepEdge({
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
}: EdgeProps) {
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
      (n: Node<NodeEditorRepresentation>) => n.id === source,
    );
    const targetNode = reactFlowRepresentation.nodes.find(
      (n: Node<NodeEditorRepresentation>) => n.id === target,
    );

    let clearanceY = Math.max(sourceY, targetY) + BOTTOM_OFFSET;

    const sourceDims: [number, number] = (sourceNode?.data
      ?.editor_dimensions as [number, number]) ?? [0, 0];
    const targetDims: [number, number] = (targetNode?.data
      ?.editor_dimensions as [number, number]) ?? [0, 0];

    const sourceHeight: number =
      sourceDims?.[1] ?? sourceNode?.measured?.height ?? 10;
    const targetHeight: number =
      targetDims?.[1] ?? targetNode?.measured?.height ?? 10;

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
