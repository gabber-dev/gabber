import { useEngine } from "@gabber/client-react";
import { useRef, useEffect } from "react";
import { LogItem } from "./LogItem"; // Assuming LogItem is in the same or imported directory

export function LogList() {
  const { logItems } = useEngine();
  const containerRef = useRef<HTMLDivElement>(null);
  const isNearBottomRef = useRef(true);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    const handleScroll = () => {
      const threshold = 100;
      const isNearBottom =
        container.scrollHeight - container.scrollTop - container.clientHeight <
        threshold;
      isNearBottomRef.current = isNearBottom;
    };

    container.addEventListener("scroll", handleScroll);
    return () => container.removeEventListener("scroll", handleScroll);
  }, []);

  useEffect(() => {
    const container = containerRef.current;
    if (!container || !isNearBottomRef.current) return;

    container.scrollTo({
      top: container.scrollHeight,
      behavior: "auto",
    });
  }, [logItems]);

  const reversedLogItems = logItems.slice().reverse();

  return (
    <div
      ref={containerRef}
      className="space-y-2 overflow-y-auto h-full bg-base-100"
    >
      {reversedLogItems.length === 0 && (
        <div className="m-2">
          <span>No log items available.</span>
        </div>
      )}
      {reversedLogItems.map((logItem, index) => (
        <LogItem key={index} logItem={logItem} />
      ))}
    </div>
  );
}
