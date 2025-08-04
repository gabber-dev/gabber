/**
 * Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
 * SPDX-License-Identifier: SUL-1.0
 */

import { GraphEditorRepresentation } from "@/generated/editor";
import {
  CreateAppRunResponse,
  DebugConnectionResponse,
  GetAppResponse,
  GetSubgraphResponse,
  ListAppsResponse,
  ListSubgraphsResponse,
  RepositoryApp,
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

export async function getExample(exampleId: string): Promise<RepositoryApp> {
  const resp = await axios.get(`${BASE_URL}/example/${exampleId}`);
  return (resp.data as GetAppResponse).app;
}

export async function listExamples(): Promise<RepositoryApp[]> {
  const resp = await axios.get(`${BASE_URL}/example/list`);
  return (resp.data as ListAppsResponse).apps;
}

export async function createAppRun({
  graph,
}: {
  graph: GraphEditorRepresentation;
}): Promise<CreateAppRunResponse> {
  const resp = await axios.post(`${BASE_URL}/app/run`, {
    type: "create_app_run",
    graph,
  });
  return resp.data;
}

export async function createDebugConnection({
  app_run,
}: {
  app_run: string;
}): Promise<DebugConnectionResponse> {
  const resp = await axios.post(`${BASE_URL}/app/debug_connection`, {
    type: "create_debug_connection",
    app_run,
  });
  return resp.data;
}
