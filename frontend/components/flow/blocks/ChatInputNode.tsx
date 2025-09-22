/**
 * Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
 * SPDX-License-Identifier: SUL-1.0
 */

import { NodeEditorRepresentation } from "@/generated/editor";
import { useState } from "react";
import { StatelessPad } from "./components/pads/StatelessPad";
import { ChatBubbleLeftIcon } from "@heroicons/react/24/outline";
import toast from "react-hot-toast";
import { useSourcePad } from "@gabber/client-react";
import { NodeName } from "./components/NodeName";
import { NodeId } from "./components/NodeId";

export interface ChatInputNodeProps {
  data: NodeEditorRepresentation;
}

export function ChatInputNode({ data }: ChatInputNodeProps) {
  const [inputText, setInputText] = useState("");
  const { pushValue } = useSourcePad(data.id, "output");

  // Only show the output pad
  const sourcePad = data.pads.find((p) => p.type === "StatelessSourcePad");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputText.trim()) return;
    try {
      // Push raw string. Backend expects plain primitives on source pads.
      await pushValue(inputText as unknown as never);
      setInputText("");
    } catch (err) {
      console.error("[ChatInput] Failed to send message:", err);
      toast.error("Failed to send message. Please try again.");
    }
  };

  const handleKeyDown = async (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      await handleSubmit(e);
    }
  };

  return (
    <div className="min-w-64 flex flex-col bg-base-200 border-2 border-black border-b-4 border-r-4 rounded-lg relative">
      <div className="flex w-full items-center gap-2 bg-base-300 border-b-2 border-black p-3 rounded-t-lg drag-handle cursor-grab active:cursor-grabbing">
        <ChatBubbleLeftIcon className="h-5 w-5 text-accent" />
        <div className="flex-1">
          <NodeName />
          <NodeId />
        </div>
        {/* no debug UI */}
      </div>

      <div className="flex flex-1 flex-col gap-2 p-4 nodrag cursor-default">
        <form onSubmit={handleSubmit} className="flex gap-2">
          <input
            type="text"
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Type a message..."
            className="input input-bordered input-sm flex-1 bg-base-300 border-2 border-black border-b-4 border-r-4 rounded-lg text-base-content placeholder-base-content/40 focus:border-primary focus:ring-2 focus:ring-primary font-vt323 text-sm hover:bg-base-100 transition-colors duration-150"
          />
          <button
            type="submit"
            disabled={!inputText.trim()}
            className="btn btn-primary btn-sm"
          >
            Send
          </button>
        </form>

        {sourcePad && (
          <div>
            <StatelessPad data={sourcePad} notes={[]} />
          </div>
        )}
      </div>
    </div>
  );
}
