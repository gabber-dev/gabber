/**
 * Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
 * SPDX-License-Identifier: SUL-1.0
 */

import {
  GetAppResponse,
  GetSubgraphResponse,
  ListAppsResponse,
  ListSubgraphsResponse,
  RepositorySubGraph,
  SaveAppRequest,
  SaveAppResponse,
  SaveSubgraphRequest,
  SaveSubgraphResponse,
} from "@/generated/repository";
import axios from "axios";

const BASE_URL = "http://localhost:8001";
export async function getApp(appId: string) {
  const resp = await axios.get(`${BASE_URL}/app/${appId}`);
  return (resp.data as GetAppResponse).app;
}

export async function listApps() {
  const resp = await axios.get(`${BASE_URL}/app/list`);
  return (resp.data as ListAppsResponse).apps;
}

export async function saveApp(req: SaveAppRequest) {
  req.type = "save_app";
  const resp = await axios.post(`${BASE_URL}/app`, req);
  return (resp.data as SaveAppResponse).app;
}

export async function saveSubGraph(
  params: SaveSubgraphRequest,
): Promise<RepositorySubGraph> {
  params.type = "save_subgraph";
  const resp = await axios.post(`${BASE_URL}/sub_graph`, params);
  return (resp.data as SaveSubgraphResponse).sub_graph;
}

export async function getSubGraph(
  graphId: string,
): Promise<RepositorySubGraph> {
  const resp = await axios.get(`${BASE_URL}/sub_graph/${graphId}`);
  return (resp.data as GetSubgraphResponse).sub_graph;
}

export async function listSubGraphs(): Promise<RepositorySubGraph[]> {
  const resp = await axios.get(`${BASE_URL}/sub_graph/list`);
  return (resp.data as ListSubgraphsResponse).sub_graphs;
}
