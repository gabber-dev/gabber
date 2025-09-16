/**
 * Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
 * SPDX-License-Identifier: SUL-1.0
 */

import { Node, Position } from "@xyflow/react";

type InternalLikeNode = Node & {
  measured: { width: number; height: number };
  internals: { positionAbsolute: { x: number; y: number } };
};

// Calculate the intersection of the line between the centers of two nodes
// and the rectangle (with measured width/height) of the first node
export function getNodeIntersection(
  intersectionNode: InternalLikeNode,
  targetNode: InternalLikeNode,
) {
  const { width: intersectionNodeWidth, height: intersectionNodeHeight } =
    intersectionNode.measured || { width: 10, height: 10 };
  const intersectionNodePosition = intersectionNode.internals.positionAbsolute;
  const targetPosition = targetNode.internals.positionAbsolute;

  const w = intersectionNodeWidth / 2;
  const h = intersectionNodeHeight / 2;

  const x2 = intersectionNodePosition.x + w;
  const y2 = intersectionNodePosition.y + h;
  const x1 = targetPosition.x + targetNode.measured.width / 2;
  const y1 = targetPosition.y + targetNode.measured.height / 2;

  const xx1 = (x1 - x2) / (2 * w) - (y1 - y2) / (2 * h);
  const yy1 = (x1 - x2) / (2 * w) + (y1 - y2) / (2 * h);
  const a = 1 / (Math.abs(xx1) + Math.abs(yy1));
  const xx3 = a * xx1;
  const yy3 = a * yy1;
  const x = w * (xx3 + yy3) + x2;
  const y = h * (-xx3 + yy3) + y2;

  return { x, y };
}

export function getEdgePosition(
  node: InternalLikeNode,
  point: { x: number; y: number },
) {
  const posAbs = node.internals.positionAbsolute as { x: number; y: number };
  const width = node.measured.width as number;
  const height = node.measured.height as number;

  const nx = Math.round(posAbs.x);
  const ny = Math.round(posAbs.y);
  const px = Math.round(point.x);
  const py = Math.round(point.y);

  if (px <= nx + 1) return Position.Left;
  if (px >= nx + width - 1) return Position.Right;
  if (py <= ny + 1) return Position.Top;
  if (py >= ny + height - 1) return Position.Bottom;

  return Position.Top;
}

export function getEdgeParams(
  source: InternalLikeNode,
  target: InternalLikeNode,
) {
  const sourceIntersectionPoint = getNodeIntersection(source, target);
  const targetIntersectionPoint = getNodeIntersection(target, source);

  const sourcePos = getEdgePosition(source, sourceIntersectionPoint);
  const targetPos = getEdgePosition(target, targetIntersectionPoint);

  return {
    sx: sourceIntersectionPoint.x,
    sy: sourceIntersectionPoint.y,
    tx: targetIntersectionPoint.x,
    ty: targetIntersectionPoint.y,
    sourcePos,
    targetPos,
  };
}
