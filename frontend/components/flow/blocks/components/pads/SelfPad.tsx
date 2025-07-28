/**
 * Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
 * SPDX-License-Identifier: SUL-1.0
 */

import { PadEditorRepresentation } from "@/generated/editor";
import { Handle, Position } from "@xyflow/react";
import { useState } from "react";

type Props = {
  nodeId: string;
  data: PadEditorRepresentation;
};
export function SelfPad({ data, nodeId }: Props) {
  return (
    <div className={`relative w-full flex items-center`}>
      <div className="w-full flex flex-col gap-2">
        <div className={`relative w-full flex gap-2 items-center justify-end`}>
          <div className={`absolute`}>
            <PadHandle data={data} nodeId={nodeId} />
          </div>
        </div>
      </div>
    </div>
  );
}

export function PadHandle({ data }: Props) {
  const [isModalOpen, setIsModalOpen] = useState(false);

  return (
    <div
      className="relative items-center justify-center"
      onMouseEnter={() => setIsModalOpen(true)}
      onMouseLeave={() => setIsModalOpen(false)}
    >
      <Handle
        className="!w-2 !h-2 !border-6 !border-transparent !box-content !bg-primary !bg-clip-padding"
        type={"source"}
        position={Position.Right}
        id={data.id}
      />
      {isModalOpen && (
        <div
          className={`absolute z-20 -left-54 -top-2 w-52 bg-base-200 border-2 border-primary rounded-lg shadow-lg p-3 text-sm`}
        >
          <div className="space-y-2">
            <div className="border-b border-primary/30 pb-2">
              <h3 className="text-accent font-medium">Pad Info</h3>
            </div>
            <div className="space-y-1">
              <div className="flex justify-between items-start">
                <span className="text-primary font-medium text-xs">ID:</span>
                <span className="text-accent text-xs break-all ml-2">
                  {data.id}
                </span>
              </div>
              <div className="flex justify-between items-start">
                <span className="text-primary font-medium text-xs">Type:</span>
                <span className="text-accent text-xs break-all ml-2">
                  {data.type}
                </span>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
