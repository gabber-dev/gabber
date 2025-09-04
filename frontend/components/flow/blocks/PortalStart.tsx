/**
 * Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
 * SPDX-License-Identifier: SUL-1.0
 */

import { Portal } from "@/generated/editor";

export interface BaseBlockProps {
  data: Portal;
}

export function PortalStart({ data }: BaseBlockProps) {
  return <div>Portal Start</div>;
}
