/**
 * Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
 * SPDX-License-Identifier: SUL-1.0
 */

import { ConnectionLineComponent, Node, Position } from "@xyflow/react";
import { useEditor } from "@/hooks/useEditor";

const HANDLE_OFFSET = 20;
const BOTTOM_OFFSET = 80;

export const CustomConnectionLine: ConnectionLineComponent = ({
  fromX,
  fromY,
  toX,
  toY,
  fromPosition,
  toPosition,
  fromNode,
}) => {
  const { reactFlowRepresentation } = useEditor();

  const isBackward = fromX > toX;
  const isSourceRight = fromPosition === Position.Right;
  const isTargetLeft = toPosition === Position.Left;

  const sourceExitX = isSourceRight
    ? fromX + HANDLE_OFFSET
    : fromX - HANDLE_OFFSET;
  const targetApproachX = isTargetLeft
    ? toX - HANDLE_OFFSET
    : toX + HANDLE_OFFSET;

  let edgePath: string;
  if (isBackward && isSourceRight && fromNode) {
    const sourceNode = reactFlowRepresentation.nodes.find(
      (n: Node) => n.id === fromNode.id,
    );
    let sourceBottomY = fromY + BOTTOM_OFFSET;

    if (sourceNode && sourceNode.measured) {
      sourceBottomY =
        sourceNode.position.y + (sourceNode.measured?.height || 10) + 20;
    }

    edgePath = `M ${fromX},${fromY}
                L ${sourceExitX},${fromY}
                L ${sourceExitX},${sourceBottomY}
                L ${targetApproachX},${sourceBottomY}
                L ${targetApproachX},${toY}
                L ${toX},${toY}`;
  } else {
    edgePath = `M ${fromX},${fromY}
                L ${sourceExitX},${fromY}
                L ${sourceExitX},${toY}
                L ${targetApproachX},${toY}
                L ${toX},${toY}`;
  }

  return (
    <g>
      <path
        d={edgePath}
        stroke="#FCD34D"
        strokeWidth={2}
        fill="none"
        strokeDasharray="5,5"
      />
    </g>
  );
};
