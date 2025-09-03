/**
 * Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
 * SPDX-License-Identifier: SUL-1.0
 */

import { createDebugConnection } from "@/lib/repository";
import { ClientPage } from "./client_page";

export default async function Page({
  params,
}: {
  params: Promise<{ run_id: string }>;
}) {
  const { run_id } = await params;
  const { graph, connection_details } = await createDebugConnection({
    run_id,
  });
  return <ClientPage graph={graph} connectionDetails={connection_details} />;
}
