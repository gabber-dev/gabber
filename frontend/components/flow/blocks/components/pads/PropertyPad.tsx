/**
 * Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
 * SPDX-License-Identifier: SUL-1.0
 */

import { PadEditorRepresentation } from "../../../../../generated/editor_server";
import { usePropertyPad } from "./hooks/usePropertyPad";
import { PadHandle } from "./PadHandle";
import { PropertyEdit } from "./property_edit/PropertyEdit";

type Props = {
  nodeId: string;
  data: PadEditorRepresentation;
};
export function PropertyPad({ data, nodeId }: Props) {
  const isSource = data.type.indexOf("Source") !== -1;

  const { singleAllowedType } = usePropertyPad(nodeId, data.id);

  return (
    <div className={`relative w-full flex items-center`}>
      <div className="w-full flex flex-col gap-2">
        <div
          className={`relative w-full flex gap-2 items-center ${isSource ? "justify-end" : "justify-start"}`}
        >
          <div className="text-sm text-accent font-medium">{data.id}</div>
          <div className={`absolute ${isSource ? "-right-4" : "-left-4"}`}>
            <PadHandle data={data} />
          </div>
        </div>
        <PropertyEdit padId={data.id} nodeId={nodeId} />
      </div>
    </div>
  );
}
