/**
 * Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
 * SPDX-License-Identifier: SUL-1.0
 */

import { useEngine } from "@gabber/client-react";
import { useRef, useEffect } from "react";
import { LogItem } from "./LogItem"; // Assuming LogItem is in the same or imported directory
import { XCircleIcon } from "@heroicons/react/24/outline";

export function LogList() {
  const { logItems, clearLogItems } = useEngine();
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
    <div className="h-full flex flex-col">
      <div className="p-1 bg-base-300 border-b border-base-300 flex">
        <button
          className="btn rounded-full btn-xs m-0 p-0 w-6 h-6 text-error"
          onClick={clearLogItems}
        >
          <XCircleIcon className="w-5 h-5" />
        </button>
      </div>
      <div
        ref={containerRef}
        className="space-y-2 overflow-y-auto flex-1 bg-base-100"
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
    </div>
  );
}
