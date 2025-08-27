/**
 * Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
 * SPDX-License-Identifier: SUL-1.0
 */

import { getSubGraph, getPreMadeSubGraph } from "@/lib/repository";
import { ClientPage } from "./client_page";

export default async function Page({
  params,
}: {
  params: Promise<{ graph: string }>;
}) {
  const { graph } = await params;

  let subgraph;
  try {
    // First try to load as a regular user subgraph
    subgraph = await getSubGraph(graph);
  } catch (error) {
    // If that fails, try to load as a pre-made subgraph
    try {
      subgraph = await getPreMadeSubGraph(graph);
    } catch (premadeError) {
      // If both fail, rethrow the original error
      throw error;
    }
  }

  return <ClientPage initialSubGraph={subgraph} />;
}
