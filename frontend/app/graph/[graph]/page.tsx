/**
 * Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
 * SPDX-License-Identifier: SUL-1.0
 */

import { getAppApi } from "@/lib/api";
import { ClientPage } from "./client_page";

export default async function Page({
  params,
}: {
  params: Promise<{ project_id: string; graph: string }>;
}) {
  const { project_id, graph } = await params;
  const appApi = await getAppApi(project_id);
  const sgResp = await appApi.getSubGraph(graph);
  const sg = sgResp.data;
  return <ClientPage initialSubGraph={sg} />;
}
