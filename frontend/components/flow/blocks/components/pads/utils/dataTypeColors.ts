/**
 * Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
 * SPDX-License-Identifier: SUL-1.0
 */

import { PadConstraint } from "@/generated/editor";

export interface DataTypeColor {
  background: string;
  border: string;
  text: string;
}

export const DATA_TYPE_COLORS: Record<string, DataTypeColor> = {
  // Text types
  string: {
    background: "#10b981", // emerald-500
    border: "#059669", // emerald-600
    text: "#ffffff",
  },
  enum: {
    background: "#10b981", // emerald-500
    border: "#059669", // emerald-600
    text: "#ffffff",
  },

  // Numeric types
  integer: {
    background: "#3b82f6", // blue-500
    border: "#2563eb", // blue-600
    text: "#ffffff",
  },
  float: {
    background: "#6366f1", // indigo-500
    border: "#4f46e5", // indigo-600
    text: "#ffffff",
  },

  // Boolean type
  boolean: {
    background: "#f59e0b", // amber-500
    border: "#d97706", // amber-600
    text: "#ffffff",
  },

  // Media types
  audio: {
    background: "#8b5cf6", // violet-500
    border: "#7c3aed", // violet-600
    text: "#ffffff",
  },
  video: {
    background: "#ec4899", // pink-500
    border: "#db2777", // pink-600
    text: "#ffffff",
  },
  audio_clip: {
    background: "#8b5cf6", // violet-500
    border: "#7c3aed", // violet-600
    text: "#ffffff",
  },
  video_clip: {
    background: "#ec4899", // pink-500
    border: "#db2777", // pink-600
    text: "#ffffff",
  },
  av_clip: {
    background: "#f97316", // orange-500
    border: "#ea580c", // orange-600
    text: "#ffffff",
  },
  image: {
    background: "#06b6d4", // cyan-500
    border: "#0891b2", // cyan-600
    text: "#ffffff",
  },

  // Context and messaging types
  context_message: {
    background: "#06b6d4", // cyan-500
    border: "#0891b2", // cyan-600
    text: "#ffffff",
  },
  context_message_role: {
    background: "#06b6d4", // cyan-500
    border: "#0891b2", // cyan-600
    text: "#ffffff",
  },

  // List and collection types
  list: {
    background: "#84cc16", // lime-500
    border: "#65a30d", // lime-600
    text: "#ffffff",
  },

  // Trigger type
  trigger: {
    background: "#ef4444", // red-500
    border: "#dc2626", // red-600
    text: "#ffffff",
  },

  // Reference types
  node_reference: {
    background: "#6b7280", // gray-500
    border: "#4b5563", // gray-600
    text: "#ffffff",
  },

  // Schema and object types
  schema: {
    background: "#a855f7", // purple-500
    border: "#9333ea", // purple-600
    text: "#ffffff",
  },
  object: {
    background: "#a855f7", // purple-500
    border: "#9333ea", // purple-600
    text: "#ffffff",
  },

  // Secret type
  secret: {
    background: "#dc2626", // red-600
    border: "#b91c1c", // red-700
    text: "#ffffff",
  },

  // Computer vision types
  bounding_box: {
    background: "#059669", // emerald-600
    border: "#047857", // emerald-700
    text: "#ffffff",
  },
  point: {
    background: "#059669", // emerald-600
    border: "#047857", // emerald-700
    text: "#ffffff",
  },
  text_labels: {
    background: "#059669", // emerald-600
    border: "#047857", // emerald-700
    text: "#ffffff",
  },
  clip_results: {
    background: "#059669", // emerald-600
    border: "#047857", // emerald-700
    text: "#ffffff",
  },

  // Default for unknown types
  default: {
    background: "#6b7280", // gray-500
    border: "#4b5563", // gray-600
    text: "#ffffff",
  },
};

export function getDataTypeColor(dataType: string): DataTypeColor {
  return DATA_TYPE_COLORS[dataType] || DATA_TYPE_COLORS.default;
}

export function getPrimaryDataType(
  allowedTypes: PadConstraint[],
): string | undefined {
  if (!allowedTypes || allowedTypes.length === 0) {
    return undefined;
  }

  // If there's only one type, return it
  if (allowedTypes.length === 1) {
    const type = allowedTypes[0];
    return typeof type === "string"
      ? type
      : type && typeof type === "object" && "type" in type
        ? type.type
        : undefined;
  }

  // For multiple types, try to find a common type or return the first one
  const typeNames = allowedTypes
    .map((type) =>
      typeof type === "string"
        ? type
        : type && typeof type === "object" && "type" in type
          ? type.type
          : undefined,
    )
    .filter(Boolean);

  return typeNames.length > 0 ? typeNames[0] : undefined;
}
