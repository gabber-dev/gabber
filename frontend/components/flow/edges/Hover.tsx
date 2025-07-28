/**
 * Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
 * SPDX-License-Identifier: SUL-1.0
 */

import {
  getBezierPath,
  BaseEdge,
  getSmoothStepPath,
  getStraightPath,
} from "@xyflow/react";
import { useState, useEffect, useCallback } from "react";

interface HoverEdgeProps {
  id: string;
  sourceX: number;
  sourceY: number;
  targetX: number;
  targetY: number;
  sourcePosition: any;
  targetPosition: any;
  source: string;
  target: string;
  sourceHandle?: string;
  targetHandle?: string;
  data?: any;
}

export function HoverEdge({
  id,
  sourceX,
  sourceY,
  targetX,
  targetY,
  source,
  target,
  sourceHandle,
  targetHandle,
}: HoverEdgeProps) {
  const [isVisible, setIsVisible] = useState(false);

  const [edgePath] = getStraightPath({
    sourceX,
    sourceY,
    // sourcePosition,
    targetX,
    targetY,
    // targetPosition,
  });

  const handleMouseEnter = useCallback(() => setIsVisible(true), []);
  const handleMouseLeave = useCallback(() => setIsVisible(false), []);

  useEffect(() => {
    const sourceHandleSelector = sourceHandle
      ? `[data-id="${source}"] .react-flow__handle[data-handleid="${sourceHandle}"]`
      : `[data-id="${source}"] .react-flow__handle-right, [data-id="${source}"] .react-flow__handle.source`;

    const targetHandleSelector = targetHandle
      ? `[data-id="${target}"] .react-flow__handle[data-handleid="${targetHandle}"]`
      : `[data-id="${target}"] .react-flow__handle-left, [data-id="${target}"] .react-flow__handle.target`;

    const sourceHandleElement = document.querySelector(sourceHandleSelector);
    const targetHandleElement = document.querySelector(targetHandleSelector);

    if (sourceHandleElement) {
      sourceHandleElement.addEventListener("mouseenter", handleMouseEnter);
      sourceHandleElement.addEventListener("mouseleave", handleMouseLeave);
    }
    if (targetHandleElement) {
      targetHandleElement.addEventListener("mouseenter", handleMouseEnter);
      targetHandleElement.addEventListener("mouseleave", handleMouseLeave);
    }

    return () => {
      if (sourceHandleElement) {
        sourceHandleElement.removeEventListener("mouseenter", handleMouseEnter);
        sourceHandleElement.removeEventListener("mouseleave", handleMouseLeave);
      }
      if (targetHandleElement) {
        targetHandleElement.removeEventListener("mouseenter", handleMouseEnter);
        targetHandleElement.removeEventListener("mouseleave", handleMouseLeave);
      }
    };
  }, [
    source,
    target,
    sourceHandle,
    targetHandle,
    handleMouseEnter,
    handleMouseLeave,
  ]);

  if (!isVisible) {
    return null;
  }

  return (
    <BaseEdge
      path={edgePath}
      style={{
        stroke: "#f59e0b",
        strokeWidth: 2,
        strokeDasharray: "3,3",
        opacity: 0.8,
      }}
    />
  );
}
