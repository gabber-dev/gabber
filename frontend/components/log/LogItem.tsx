import { RuntimeEventPayload_LogItem } from "@gabber/client-react";

type Props = {
  logItem: RuntimeEventPayload_LogItem;
};

const levelToAlertClass = (level: string): string => {
  switch (level.toLowerCase()) {
    case "error":
      return "alert-error";
    case "warn":
    case "warning":
      return "alert-warning";
    case "success":
      return "alert-success";
    case "info":
    default:
      return "alert-info";
  }
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

export function LogItem({ logItem }: Props) {
  const { message, level, timestamp, node, subgraph, pad, ...extra } = logItem;
  const alertClass = levelToAlertClass(level);
  const badgeClass = levelToBadgeClass(level);

  return (
    <div className={`alert ${alertClass} shadow-lg`}>
      <div className="flex flex-col w-full">
        {/* Header: Level, Message, and Timestamp on the same line */}
        <div className="flex justify-between items-start gap-2">
          <div className="flex items-center gap-2 flex-1 min-w-0">
            <div className={`badge ${badgeClass} gap-2`}>
              {level.toUpperCase()}
            </div>
            <p className="font-mono flex-1 min-w-0 break-words">
              {typeof message === "string" ? message : JSON.stringify(message)}
            </p>
          </div>
          <div className="text-xs opacity-75 font-mono flex-shrink-0">
            {new Date(timestamp).toLocaleString()}
          </div>
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
