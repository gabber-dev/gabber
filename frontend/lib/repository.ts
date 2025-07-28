/**
 * Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
 * SPDX-License-Identifier: SUL-1.0
 */

import { RepositoryApp, SaveAppRequest } from "@/generated/repository";
import axios from "axios";

const BASE_URL = "http://localhost:8001";

export async function listApps(): Promise<RepositoryApp[]> {
  const resp = await axios.get(`${BASE_URL}/app/list`);
  return resp.data as RepositoryApp[];
}

export async function getApp(appId: string): Promise<RepositoryApp> {
  const resp = await axios.get(`${BASE_URL}/app/${appId}`);
  return resp.data as RepositoryApp;
}

export async function listSubgraphs(): Promise<RepositoryApp[]> {
  const resp = await axios.get(`${BASE_URL}/subgraph/list`);
  return resp.data as RepositoryApp[];
}

export async function saveApp(req: SaveAppRequest) {
  await axios.post(`${BASE_URL}/app/save`, req);
}
