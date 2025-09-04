/**
 * Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
 * SPDX-License-Identifier: SUL-1.0
 */

import { Portal, PortalEnd as PortalEndModel } from "@/generated/editor";

export interface BaseBlockProps {
  data: PortalEndModel;
}

export function PortalEnd({ data }: BaseBlockProps) {
  return <div>Portal End</div>;
}
