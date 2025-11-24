/**
 * Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
 * SPDX-License-Identifier: SUL-1.0
 */

import { useEngine } from "@gabber/client-react";
import { useNodeId } from "@xyflow/react";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { BaseBlockProps } from "./BaseBlock";
import { CubeIcon } from "@heroicons/react/24/outline";
import { NodeName } from "./components/NodeName";
import { NodeId } from "./components/NodeId";
import { SelfPad } from "./components/pads/SelfPad";
import ReactModal from "react-modal";
import { ToolGroupEditModal } from "@/components/tool/ToolGroupEditModal";

export function ToolGroupNode({ data }: BaseBlockProps) {
  const [modalOpen, setModalOpen] = useState(false);
  const selfPad = useMemo(() => {
    return data.pads.find(
      (p) => p.type === "PropertySourcePad" && p.id === "self",
    );
  }, [data]);
  return (
    <div className="w-80 flex flex-col bg-base-200 border-2 border-black border-b-4 border-r-4 rounded-lg relative">
      <ReactModal
        isOpen={modalOpen}
        onRequestClose={() => setModalOpen(false)}
        overlayClassName="fixed top-0 bottom-0 left-0 right-0 backdrop-blur-lg bg-blur flex justify-center items-center z-11"
        shouldCloseOnOverlayClick={true}
      >
        <ToolGroupEditModal
          toolGroup={data.toolGroup}
          onClose={() => setModalOpen(false)}
          onSave={() => {}}
        />
      </ReactModal>
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
      <div className="flex flex-col gap-1 p-1">
        <button
          className="btn btn-sm btn-ghost gap-1"
          onClick={() => {
            setModalOpen(true);
          }}
        >
          Edit Tools
        </button>
      </div>

      <div className="flex flex-1 flex-col gap-2 p-4 nodrag cursor-default"></div>
    </div>
  );
}
