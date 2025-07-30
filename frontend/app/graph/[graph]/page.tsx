/**
 * Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
 * SPDX-License-Identifier: SUL-1.0
 */

import { getSubGraph } from "@/lib/repository";
import { ClientPage } from "./client_page";

export default async function Page({
  params,
}: {
  params: Promise<{ graph: string }>;
}) {
  const { graph } = await params;
  const subgraph = await getSubGraph(graph);
  return <ClientPage initialSubGraph={subgraph} />;
}
