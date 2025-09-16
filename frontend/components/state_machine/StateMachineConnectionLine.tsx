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

  const targetNode = {
    id: "__connection_target__",
    measured: { width: 1, height: 1 },
    internals: { positionAbsolute: { x: toX, y: toY } },
  };

  const { sx, sy, tx, ty, sourcePos, targetPos } = getEdgeParams(
    fromNode,
    targetNode,
  );

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
