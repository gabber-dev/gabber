/**
 * Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
 * SPDX-License-Identifier: SUL-1.0
 */

import { GraphEditorRepresentation } from "@/generated/editor";
import {
  AppExport,
  DebugConnectionResponse,
  ExportAppResponse,
  ExportSubGraphResponse,
  GetAppResponse,
  GetSubgraphResponse,
  ListAppsResponse,
  ListSubgraphsResponse,
  PublicSecret,
  RepositoryApp,
  RepositorySubGraph,
  SaveAppRequest,
  SaveAppResponse,
  SaveSubgraphRequest,
  SaveSubgraphResponse,
  SubGraphExport,
} from "@/generated/repository";
import { ConnectionDetails } from "@gabber/client-react";
import axios from "axios";
import { v4 } from "uuid";

function getBaseUrl() {
  const host = process.env.REPOSITORY_HOST;
  const publicHost = process.env.GABBER_PUBLIC_HOST;
  if (host) {
    return `http://${host}`;
  }
  return `http://${publicHost || "localhost"}:8001`;
}

export function getEditorUrl() {
  if (typeof window !== "undefined") {
    throw new Error("getEditorUrl should only be called on the server");
  }
  const publicHost = process.env.GABBER_PUBLIC_HOST;
  return `ws://${publicHost || "localhost"}:8000/ws`;
}

export async function getApp(appId: string) {
  const resp = await axios.get(`${getBaseUrl()}/app/${appId}`);
  return (resp.data as GetAppResponse).app;
}

export async function listApps() {
  const resp = await axios.get(`${getBaseUrl()}/app/list`);
  return (resp.data as ListAppsResponse).apps;
}

export async function saveApp(req: SaveAppRequest) {
  req.type = "save_app";
  const resp = await axios.post(`${getBaseUrl()}/app`, req);
  return (resp.data as SaveAppResponse).app;
}

export async function deleteApp(appId: string) {
  await axios.delete(`${getBaseUrl()}/app/${appId}`);
}

export async function saveSubGraph(
  params: SaveSubgraphRequest,
): Promise<RepositorySubGraph> {
  params.type = "save_subgraph";
  const resp = await axios.post(`${getBaseUrl()}/sub_graph`, params);
  return (resp.data as SaveSubgraphResponse).sub_graph;
}

export async function deleteSubGraph(graphId: string) {
  await axios.delete(`${getBaseUrl()}/sub_graph/${graphId}`);
}

export async function getSubGraph(
  graphId: string,
): Promise<RepositorySubGraph> {
  const resp = await axios.get(`${getBaseUrl()}/sub_graph/${graphId}`);
  return (resp.data as GetSubgraphResponse).sub_graph;
}

export async function listSubGraphs(): Promise<RepositorySubGraph[]> {
  const resp = await axios.get(`${getBaseUrl()}/sub_graph/list`);
  return (resp.data as ListSubgraphsResponse).sub_graphs;
}

export async function getExample(exampleId: string): Promise<RepositoryApp> {
  const resp = await axios.get(`${getBaseUrl()}/example/${exampleId}`);
  return (resp.data as GetAppResponse).app;
}

export async function listExamples(): Promise<RepositoryApp[]> {
  const resp = await axios.get(`${getBaseUrl()}/example/list`);
  return (resp.data as ListAppsResponse).apps;
}

export async function getPreMadeSubGraph(
  subgraphId: string,
): Promise<RepositorySubGraph> {
  const resp = await axios.get(
    `${getBaseUrl()}/premade_subgraph/${subgraphId}`,
  );
  return (resp.data as GetSubgraphResponse).sub_graph;
}
export async function listPreMadeSubGraphs(): Promise<RepositorySubGraph[]> {
  const resp = await axios.get(`${getBaseUrl()}/premade_subgraph/list`);
  return (resp.data as ListSubgraphsResponse).sub_graphs;
}

export async function createAppRun({
  graph,
}: {
  graph: GraphEditorRepresentation;
}): Promise<{ connectionDetails: ConnectionDetails; runId: string }> {
  const run_id = v4();
  const resp = await axios.post(`${getBaseUrl()}/app/run`, {
    type: "create_app_run",
    graph,
    run_id,
  });

  return {
    connectionDetails: resp.data.connection_details,
    runId: run_id,
  };
}

export async function createDebugConnection({
  run_id,
}: {
  run_id: string;
}): Promise<DebugConnectionResponse> {
  const resp = await axios.post(`${getBaseUrl()}/app/debug_connection`, {
    type: "create_debug_connection",
    run_id,
  });
  return resp.data;
}

export async function importApp(app: AppExport): Promise<RepositoryApp> {
  const resp = await axios.post(`${getBaseUrl()}/app/import`, app);
  return resp.data as RepositoryApp;
}

export async function exportApp(appId: string): Promise<AppExport> {
  const resp = await axios.get(`${getBaseUrl()}/app/${appId}/export`);
  return (resp.data as ExportAppResponse).export;
}

export async function importSubGraph(
  subgraph: SubGraphExport,
): Promise<RepositorySubGraph> {
  const resp = await axios.post(`${getBaseUrl()}/sub_graph/import`, subgraph);
  return resp.data as RepositorySubGraph;
}

export async function exportSubGraph(
  subgraphId: string,
): Promise<SubGraphExport> {
  const resp = await axios.get(
    `${getBaseUrl()}/sub_graph/${subgraphId}/export`,
  );
  return (resp.data as ExportSubGraphResponse).export;
}

export async function listSecrets(): Promise<PublicSecret[]> {
  const resp = await axios.get(`${getBaseUrl()}/secret/list`);
  return resp.data.secrets;
}

export async function addSecret(name: string, value: string): Promise<void> {
  await axios.post(`${getBaseUrl()}/secret`, {
    type: "add_secret",
    name,
    value,
  });
}

export async function updateSecret(
  id: string,
  name: string,
  value: string,
): Promise<void> {
  // In the current implementation, id and name are the same for local deployment
  // If the name has changed, we need to delete the old secret and create a new one
  if (id !== name) {
    // Delete the old secret
    await axios.delete(`${getBaseUrl()}/secret/${encodeURIComponent(id)}`);
    // Create a new secret with the new name
    await axios.post(`${getBaseUrl()}/secret`, {
      type: "add_secret",
      name,
      value,
    });
  } else {
    // Just update the value
    await axios.put(`${getBaseUrl()}/secret/${encodeURIComponent(name)}`, {
      type: "update_secret",
      value,
    });
  }
}

export async function deleteSecret(id: string): Promise<void> {
  await axios.delete(`${getBaseUrl()}/secret/${encodeURIComponent(id)}`);
}
