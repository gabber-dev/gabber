import { useEngine } from "@gabber/client-react";
import { LogItem } from "./LogItem"; // Assuming LogItem is in the same or imported directory

export function LogList() {
  const { logItems } = useEngine();

  return (
    <div className="space-y-2 overflow-y-auto h-full bg-base-100">
      {logItems?.length === 0 && (
        <div className="m-2">
          <span>No log items available.</span>
        </div>
      )}
      {logItems.map((logItem, index) => (
        <LogItem key={index} logItem={logItem} />
      ))}
    </div>
  );
}
