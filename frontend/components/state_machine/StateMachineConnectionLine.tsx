/**
 * Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
 * SPDX-License-Identifier: SUL-1.0
 */

import {
  ConnectionLineComponent,
  getBezierPath,
  Position,
} from "@xyflow/react";

export const StateMachineConnectionLine: ConnectionLineComponent = ({
  fromX,
  fromY,
  toX,
  toY,
  fromPosition,
  toPosition,
}) => {
  // offsets not used with bezier path, but kept for potential step routing
  // const HANDLE_OFFSET = 20;
  // const sourceExitX =
  //   fromPosition === Position.Right
  //     ? fromX + HANDLE_OFFSET
  //     : fromX - HANDLE_OFFSET;
  // const targetApproachX =
  //   toPosition === Position.Left ? toX - HANDLE_OFFSET : toX + HANDLE_OFFSET;

  const [path] = getBezierPath({
    sourceX: fromX,
    sourceY: fromY,
    sourcePosition: fromPosition,
    targetX: toX,
    targetY: toY,
    targetPosition: toPosition,
  });

  // Simple arrowhead at the current tip
  const arrowPoints = (() => {
    const size = 6;
    switch (toPosition) {
      case Position.Left:
        return `${toX},${toY} ${toX + size},${toY - size / 2} ${toX + size},${toY + size / 2}`;
      case Position.Right:
        return `${toX},${toY} ${toX - size},${toY - size / 2} ${toX - size},${toY + size / 2}`;
      case Position.Top:
        return `${toX},${toY} ${toX - size / 2},${toY + size} ${toX + size / 2},${toY + size}`;
      case Position.Bottom:
      default:
        return `${toX},${toY} ${toX - size / 2},${toY - size} ${toX + size / 2},${toY - size}`;
    }
  })();

  return (
    <g>
      <path
        d={path}
        stroke="#F59E0B"
        strokeWidth={2.5}
        fill="none"
        strokeDasharray="5,5"
      />
      <polygon points={arrowPoints} fill="#F59E0B" />
    </g>
  );
};

export default StateMachineConnectionLine;
