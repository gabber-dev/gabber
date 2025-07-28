/**
 * Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
 * SPDX-License-Identifier: SUL-1.0
 */

import { ClientPage } from "./client_page";
import { listApps, listSubgraphs } from "@/lib/repository";

export default async function Page() {
  const apps = await listApps();
  const subgraphs = await listSubgraphs();

  return <ClientPage initialApps={apps} initialSubGraphs={subgraphs} />;
}
