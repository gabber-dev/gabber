/**
 * Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
 * SPDX-License-Identifier: SUL-1.0
 */

import { BaseBlockProps } from "./BaseBlock";
import { usePropertyPad } from "./components/pads/hooks/usePropertyPad";
import {
  CubeIcon,
  ChevronDownIcon,
  ChevronUpIcon,
  ClipboardDocumentIcon,
} from "@heroicons/react/24/outline";
import { NodeName } from "./components/NodeName";
import { NodeId } from "./components/NodeId";
import { PropertyPad } from "./components/pads/PropertyPad";
import { StatelessPad } from "./components/pads/StatelessPad";
import { SelfPad } from "./components/pads/SelfPad";
import { useMemo, useState, useRef } from "react";
import toast from "react-hot-toast";

interface ToolCall {
  call_id?: string;
  [key: string]: unknown;
}

interface ContextMessage {
  role: "user" | "assistant" | "system" | "tool";
  content: Array<{
    type?: string;
    content?: string;
    text?: string;
  }>;
  tool_calls?: Array<ToolCall>;
  tool_call_id?: string | null;
}

function MessageItem({
  message,
  index,
}: {
  message: ContextMessage;
  index: number;
}) {
  const roleColors = {
    system: "bg-purple-900/30 border-purple-500",
    user: "bg-blue-900/30 border-blue-500",
    assistant: "bg-green-900/30 border-green-500",
    tool: "bg-orange-900/30 border-orange-500",
  };

  const roleLabels = {
    system: "System",
    user: "User",
    assistant: "Assistant",
    tool: "Tool",
  };

  // Process content items to show text and media indicators
  console.log("Processing message content:", message.content);
  const contentItems = message.content.map((item, idx) => {
    if (typeof item === "string") {
      return { type: "text", content: item, key: idx };
    }

    const type = item.type?.toLowerCase() || "";

    if (type === "image" || type.includes("image")) {
      return { type: "image", content: "🖼️ Image", key: idx };
    }
    if (type === "video" || type.includes("video")) {
      return { type: "video", content: "🎥 Video", key: idx };
    }
    if (type === "audio" || type.includes("audio")) {
      return { type: "audio", content: "🎵 Audio", key: idx };
    }

    // Default to text
    const textContent = item.content || item.text || "";
    return { type: "text", content: textContent, key: idx };
  });

  const hasToolCalls = message.tool_calls && message.tool_calls.length > 0;
  const hasToolCallId = message.tool_call_id;

  return (
    <div
      className={`p-2 rounded border ${roleColors[message.role]} mb-1 text-xs`}
    >
      <div className="flex items-center gap-2 mb-1">
        <span className="font-bold uppercase">{roleLabels[message.role]}</span>
        <span className="text-base-content/50">#{index}</span>
      </div>

      <div className="space-y-1">
        {contentItems.map((item) => (
          <div key={item.key} className="break-words overflow-hidden">
            {item.type === "text" ? (
              <span className="whitespace-pre-wrap">{item.content}</span>
            ) : (
              <span className="text-base-content/70 italic">
                {item.content}
              </span>
            )}
          </div>
        ))}
      </div>

      {hasToolCalls && (
        <div className="text-base-content/70 mt-1">
          🔧 {message.tool_calls!.length} tool call(s)
        </div>
      )}
      {hasToolCallId && (
        <div className="text-base-content/70 mt-1 truncate">
          Tool ID: {message.tool_call_id}
        </div>
      )}
    </div>
  );
}

export function LLMContextNode({ data }: BaseBlockProps) {
  const [showMessages, setShowMessages] = useState(false);
  const scrollContainerRef = useRef<HTMLDivElement>(null);
  const propertyPadResult = usePropertyPad<ContextMessage[]>(data.id, "source");
  const { runtimeValue: contextMessages, editorValue } = propertyPadResult;

  // Debug: log what we're getting
  console.log("LLMContext messages:", {
    contextMessages,
    editorValue,
    count: (contextMessages || editorValue || []).length,
  });

  const sinkPads = useMemo(() => {
    return data.pads.filter(
      (p) => p.type === "StatelessSinkPad" || p.type === "PropertySinkPad",
    );
  }, [data]);

  const sourcePads = useMemo(() => {
    return data.pads.filter(
      (p) =>
        p.type === "StatelessSourcePad" ||
        (p.type === "PropertySourcePad" && p.id !== "self"),
    );
  }, [data]);

  const selfPad = useMemo(() => {
    return data.pads.find(
      (p) => p.type === "PropertySourcePad" && p.id === "self",
    );
  }, [data]);

  // Use contextMessages from runtime, fallback to editorValue
  const messages = useMemo(() => {
    const msgs = contextMessages || editorValue || [];
    // Ensure it's an array
    const result = Array.isArray(msgs) ? msgs : [];
    return result;
  }, [contextMessages, editorValue]);

  const messageCount = messages.length;

  // Function to copy all messages to clipboard
  const copyAllMessages = () => {
    const roleLabels: Record<string, string> = {
      system: "SYSTEM",
      user: "USER",
      assistant: "ASSISTANT",
      tool: "TOOL",
    };

    const formattedMessages = messages
      .map((msg, idx) => {
        const role = roleLabels[msg.role] || msg.role.toUpperCase();
        const textContent = msg.content
          .map((item: { type?: string; content?: string; text?: string }) => {
            if (typeof item === "string") return item;
            const type = item.type?.toLowerCase() || "";
            if (type === "image" || type.includes("image")) return "[Image]";
            if (type === "video" || type.includes("video")) return "[Video]";
            if (type === "audio" || type.includes("audio")) return "[Audio]";
            return item.content || item.text || "";
          })
          .filter(Boolean)
          .join("\n");

        let content = `[${idx}] ${role}:\n${textContent}`;

        if (msg.tool_calls && msg.tool_calls.length > 0) {
          content += `\n[Tool calls: ${msg.tool_calls.length}]`;
        }
        if (msg.tool_call_id) {
          content += `\n[Tool ID: ${msg.tool_call_id}]`;
        }

        return content;
      })
      .join("\n\n");

    navigator.clipboard.writeText(formattedMessages).then(
      () => {
        toast.success("Context copied to clipboard!");
      },
      () => {
        toast.error("Failed to copy to clipboard");
      },
    );
  };

  // Scroll functions
  const scrollUp = () => {
    const container = scrollContainerRef.current;
    if (container) {
      container.scrollTop -= 50;
    }
  };

  const scrollDown = () => {
    const container = scrollContainerRef.current;
    if (container) {
      container.scrollTop += 50;
    }
  };

  // Check if we can scroll up or down
  const canScrollUp = () => {
    const container = scrollContainerRef.current;
    return container ? container.scrollTop > 0 : false;
  };

  const canScrollDown = () => {
    const container = scrollContainerRef.current;
    return container
      ? container.scrollTop + container.clientHeight < container.scrollHeight
      : false;
  };

  return (
    <div className="w-80 flex flex-col bg-base-200 border-2 border-black border-b-4 border-r-4 rounded-lg relative">
      <div className="flex w-full items-center gap-2 bg-base-300 border-b-2 border-black p-3 rounded-t-lg drag-handle cursor-grab active:cursor-grabbing">
        <CubeIcon className="h-5 w-5 text-accent" />
        <div className="flex-1 min-w-0">
          <NodeName />
          <NodeId />
        </div>

        <div className="absolute right-0">
          {selfPad && <SelfPad data={selfPad} nodeId={data.id} />}
        </div>
      </div>

      {/* Context Messages Viewer */}
      <div className="border-b-2 border-black">
        <div className="flex items-center bg-base-300">
          <button
            className="flex-1 px-4 py-2 flex items-center justify-between hover:bg-base-100 transition-colors nodrag"
            onClick={() => setShowMessages(!showMessages)}
          >
            <span className="text-sm font-semibold">
              Context ({messageCount})
            </span>
            {showMessages ? (
              <ChevronUpIcon className="h-4 w-4" />
            ) : (
              <ChevronDownIcon className="h-4 w-4" />
            )}
          </button>
          {messages.length > 0 && (
            <button
              className="px-3 py-2 hover:bg-base-100 transition-colors nodrag"
              onClick={copyAllMessages}
              title="Copy all messages"
            >
              <ClipboardDocumentIcon className="h-4 w-4" />
            </button>
          )}
        </div>
        {showMessages && (
          <div className="relative">
            {/* Scroll Up Button */}
            <button
              onClick={scrollUp}
              disabled={!canScrollUp()}
              className="absolute top-2 right-2 z-10 p-1 rounded bg-base-200 hover:bg-base-300 disabled:opacity-50 disabled:cursor-not-allowed transition-colors nodrag"
              title="Scroll up"
            >
              <ChevronUpIcon className="h-4 w-4" />
            </button>

            {/* Messages Container */}
            <div
              className="h-64 p-2 bg-base-100 nodrag overflow-y-auto"
              style={{
                scrollbarWidth: "thin",
                scrollbarColor: "rgb(156 163 175) transparent",
              }}
              ref={scrollContainerRef}
            >
              {messages.length === 0 ? (
                <div className="text-xs text-center text-base-content/50 py-4">
                  No messages yet
                </div>
              ) : (
                messages.map((message, index) => (
                  <MessageItem key={index} message={message} index={index} />
                ))
              )}
            </div>

            {/* Scroll Down Button */}
            <button
              onClick={scrollDown}
              disabled={!canScrollDown()}
              className="absolute bottom-2 right-2 z-10 p-1 rounded bg-base-200 hover:bg-base-300 disabled:opacity-50 disabled:cursor-not-allowed transition-colors nodrag"
              title="Scroll down"
            >
              <ChevronDownIcon className="h-4 w-4" />
            </button>
          </div>
        )}
      </div>

      <div className="flex flex-1 flex-col gap-2 p-4 nodrag cursor-default">
        {sourcePads.map((pad) => {
          if (pad.type === "StatelessSourcePad") {
            return (
              <div key={pad.id}>
                <StatelessPad
                  data={pad}
                  notes={(data.notes || []).filter(
                    (note) => note.pad === pad.id,
                  )}
                />
              </div>
            );
          } else if (pad.type === "PropertySourcePad") {
            return (
              <div key={pad.id}>
                <PropertyPad
                  nodeId={data.id}
                  data={pad}
                  notes={(data.notes || []).filter(
                    (note) => note.pad === pad.id,
                  )}
                />
              </div>
            );
          }
        })}
        {sinkPads.map((pad) => {
          if (pad.type === "StatelessSinkPad") {
            return (
              <div key={pad.id}>
                <StatelessPad
                  data={pad}
                  notes={(data.notes || []).filter(
                    (note) => note.pad === pad.id,
                  )}
                />
              </div>
            );
          } else if (pad.type === "PropertySinkPad") {
            return (
              <div key={pad.id}>
                <PropertyPad
                  nodeId={data.id}
                  data={pad}
                  notes={(data.notes || []).filter(
                    (note) => note.pad === pad.id,
                  )}
                />
              </div>
            );
          }
        })}
      </div>
    </div>
  );
}
