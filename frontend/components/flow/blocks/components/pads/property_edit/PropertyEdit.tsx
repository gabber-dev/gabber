/**
 * Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
 * SPDX-License-Identifier: SUL-1.0
 */

import { usePropertyPad } from "../hooks/usePropertyPad";
import { ContextMessageRoleEdit } from "./ContextMessageRoleEdit";
import { StringPropertyEdit } from "./StringPropertyEdit";
import { FloatPropertyEdit } from "./FloatPropertyEdit";
import { IntPropertyEdit } from "./IntPropertyEdit";
import { BooleanPropertyEdit } from "./BooleanPropertyEdit";
import { NodeReferenceEdit } from "./NodeReferenceEdit";
import { SecretPropertyEdit } from "./SecretPropertyEdit";

import { EnumPropertyEdit } from "./EnumPropertyEdit";

export type PropertyEditProps = {
  nodeId: string;
  padId: string;
};

export function PropertyEdit({ nodeId, padId }: PropertyEditProps) {
  const { singleAllowedType } = usePropertyPad(nodeId, padId);

  if (!singleAllowedType) {
    return null;
  }

  if (singleAllowedType.type === "context_message_role") {
    return <ContextMessageRoleEdit nodeId={nodeId} padId={padId} />;
  }

  if (singleAllowedType.type === "string") {
    return <StringPropertyEdit nodeId={nodeId} padId={padId} />;
  }

  if (singleAllowedType.type === "float") {
    return <FloatPropertyEdit nodeId={nodeId} padId={padId} />;
  }

  if (singleAllowedType.type === "integer") {
    return <IntPropertyEdit nodeId={nodeId} padId={padId} />;
  }

  if (singleAllowedType.type === "boolean") {
    return <BooleanPropertyEdit nodeId={nodeId} padId={padId} />;
  }

  if (singleAllowedType.type === "node_reference") {
    return <NodeReferenceEdit nodeId={nodeId} padId={padId} />;
  }

  if (singleAllowedType.type === "secret") {
    return <SecretPropertyEdit nodeId={nodeId} padId={padId} />;
  }

  if (singleAllowedType.type === "enum") {
    return <EnumPropertyEdit nodeId={nodeId} padId={padId} />;
  }

  return null;
}
