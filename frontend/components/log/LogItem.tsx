/**
 * Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
 * SPDX-License-Identifier: SUL-1.0
 */

import { RuntimeEventPayload_LogItem } from "@gabber/client-react";

type Props = {
  logItem: RuntimeEventPayload_LogItem;
  count?: number;
};

const levelToBadgeClass = (level: string): string => {
  switch (level.toLowerCase()) {
    case "error":
      return "badge-error";
    case "warn":
    case "warning":
      return "badge-warning";
    case "success":
      return "badge-success";
    case "info":
    case "debug":
    default:
      return "badge-info";
  }
};

const levelToTextClass = (level: string): string => {
  switch (level.toLowerCase()) {
    case "error":
      return "text-error";
    case "warn":
    case "warning":
      return "text-warning";
    case "success":
      return "text-success";
    case "info":
    default:
      return "text-info";
  }
};

export function LogItem({ logItem, count = 1 }: Props) {
  const { message, level, timestamp, node, subgraph, pad, ...extra } = logItem;
  const badgeClass = levelToBadgeClass(level);
  const textClass = levelToTextClass(level);

  return (
    <div className="alert shadow-lg">
      <div className="flex flex-col w-full">
        {/* Header: Level, Count Badge (if >1), Timestamp, then Message on the same line */}
        <div className="flex items-center gap-2">
          {count > 1 && (
            <div className="badge badge-neutral badge-xs">{count}x</div>
          )}
          <div className={`badge ${badgeClass} gap-2`}>
            {level.toUpperCase()}
          </div>

          <div className="text-xs opacity-75 font-mono flex-shrink-0">
            {new Date(timestamp).toLocaleTimeString()}
          </div>
          <p className={`font-mono flex-1 min-w-0 break-words ${textClass}`}>
            {typeof message === "string" ? message : JSON.stringify(message)}
          </p>
        </div>

        {/* Optional fields as badges */}
        {(node || subgraph || pad) && (
          <div className="flex flex-wrap gap-1 mt-1">
            {node && <div className="badge badge-neutral">{node}</div>}
            {subgraph && (
              <div className="badge badge-secondary">{subgraph}</div>
            )}
            {pad && <div className="badge badge-accent">{pad}</div>}
          </div>
        )}

        {/* Extra fields if any */}
        {Object.keys(extra).length > 0 && (
          <details className="collapse mt-1">
            <summary className="collapse-title text-sm font-medium">
              Additional Data
            </summary>
            <div className="collapse-content">
              <pre className="text-xs overflow-auto">
                {JSON.stringify(extra, null, 2)}
              </pre>
            </div>
          </details>
        )}
      </div>
    </div>
  );
}
