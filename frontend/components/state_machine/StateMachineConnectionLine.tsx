/**
 * Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
 * SPDX-License-Identifier: SUL-1.0
 */

import { ConnectionLineComponent, getBezierPath } from "@xyflow/react";
import { getEdgeParams } from "./floating";

export const StateMachineConnectionLine: ConnectionLineComponent = ({
  toX,
  toY,
  fromPosition,
  toPosition,
  fromNode,
}) => {
  if (!fromNode) return null;

  const fromWidth = fromNode.measured.width || 10;
  const fromHeight = fromNode.measured.height || 10;
  const fromDims = {
    position: fromNode.position,
    size: { width: fromWidth, height: fromHeight },
  };

  const { sx, sy, tx, ty, sourcePos, targetPos } = getEdgeParams(fromDims, {
    position: { x: toX, y: toY },
    size: { width: 10, height: 10 },
  });

  const [path] = getBezierPath({
    sourceX: sx,
    sourceY: sy,
    sourcePosition: sourcePos || fromPosition,
    targetPosition: targetPos || toPosition,
    targetX: tx || toX,
    targetY: ty || toY,
  });

  return (
    <g>
      <path
        d={path}
        stroke="#F59E0B"
        strokeWidth={2.5}
        fill="none"
        strokeDasharray="5,5"
      />
    </g>
  );
};

export default StateMachineConnectionLine;
