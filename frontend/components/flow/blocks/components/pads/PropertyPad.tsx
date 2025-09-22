/**
 * Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
 * SPDX-License-Identifier: SUL-1.0
 */

import { NodeNote, PadEditorRepresentation } from "@/generated/editor";
import { PadHandle } from "./PadHandle";
import { PropertyEdit } from "./property_edit/PropertyEdit";
import { usePropertyPad } from "./hooks/usePropertyPad";

type Props = {
  nodeId: string;
  data: PadEditorRepresentation;
  notes: NodeNote[];
};
export function PropertyPad({ data, nodeId, notes }: Props) {
  const isSource = data.type.indexOf("Source") !== -1;
  const { runtimeChanged } = usePropertyPad(nodeId, data.id);

  return (
    <div className={`relative w-full flex items-center`}>
      <div
        className={`w-full flex flex-row items-center gap-2 ${isSource ? "flex-row-reverse" : "flex-row"}`}
      >
        <div className="relative flex gap-2 items-center">
          {runtimeChanged && (
            <div className="flex items-center justify-center bg-secondary text-base-content text-sm pt-1 w-3 h-3 font-bold rounded-full">
              *
            </div>
          )}
          <div className="text-sm text-accent font-medium">{data.id}</div>
          <div className={`absolute ${isSource ? "-right-4" : "-left-4"}`}>
            <PadHandle notes={notes} data={data} />
          </div>
        </div>
        <div className="flex-1">
          <PropertyEdit padId={data.id} nodeId={nodeId} />
        </div>
      </div>
    </div>
  );
}
