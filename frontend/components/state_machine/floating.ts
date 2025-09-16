/**
 * Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
 * SPDX-License-Identifier: SUL-1.0
 */

import { Position } from "@xyflow/react";

type NodeDims = {
  position: { x: number; y: number };
  size: { width: number; height: number };
};

export function getNodeIntersection(
  intersectionNode: NodeDims,
  targetNode: NodeDims,
) {
  const { width: intersectionNodeWidth, height: intersectionNodeHeight } =
    intersectionNode.size || { width: 10, height: 10 };
  const intersectionNodePosition = intersectionNode.position;
  const targetPosition = targetNode.position;

  const w = (intersectionNodeWidth || 10) / 2;
  const h = (intersectionNodeHeight || 10) / 2;

  const x2 = intersectionNodePosition.x + w;
  const y2 = intersectionNodePosition.y + h;
  const x1 = targetPosition.x + (targetNode.size.width || 10) / 2;
  const y1 = targetPosition.y + (targetNode.size.height || 10) / 2;

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
  node: NodeDims,
  point: { x: number; y: number },
) {
  const posAbs = node.position;
  const width = node.size.width as number;
  const height = node.size.height as number;

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

export function getEdgeParams(source: NodeDims, target: NodeDims) {
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
