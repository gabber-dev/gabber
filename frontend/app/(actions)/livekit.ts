/**
 * Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
 * SPDX-License-Identifier: SUL-1.0
 */

"use server";
import { GraphEditorRepresentation } from "@/generated/editor";
import { getApp, getExample } from "@/lib/repository";
import {
  AccessToken,
  RoomServiceClient,
  AgentDispatchClient,
} from "livekit-server-sdk";
import { v4 as uuidv4 } from "uuid";

type CreateLivekitRoomParams = {
  appId?: string;
  exampleId?: string;
};

type ConnectionDetails = {
  url: string;
  token: string;
};

export async function createLivekitRoom({
  appId,
  exampleId,
}: CreateLivekitRoomParams): Promise<ConnectionDetails> {
  if (!appId && !exampleId) {
    throw new Error("Either appId or exampleId must be provided");
  }
  const livekitUrl = "ws://localhost:7880";
  const livekitApiKey = "devkey";
  const livekitApiSecret = "secret";
  const at = new AccessToken(livekitApiKey, livekitApiSecret, {
    identity: "human",
  });
  const roomName = uuidv4();
  at.addGrant({
    roomJoin: true,
    room: roomName,
    canPublish: true,
    canSubscribe: true,
  });
  const roomServiceClient = new RoomServiceClient(
    livekitUrl,
    livekitApiKey,
    livekitApiSecret,
  );
  const agentDispatchClient = new AgentDispatchClient(
    livekitUrl,
    livekitApiKey,
    livekitApiSecret,
  );
  await roomServiceClient.createRoom({
    name: roomName,
  });
  let graph: GraphEditorRepresentation | undefined;
  if (appId) {
    const appObj = await getApp(appId);
    graph = appObj.graph;
  } else if (exampleId) {
    const exampleApp = await getExample(exampleId);
    graph = exampleApp.graph;
  }

  await agentDispatchClient.createDispatch(roomName, "gabber-engine", {
    metadata: JSON.stringify({ graph }),
  });
  const connectionDetails = {
    url: livekitUrl,
    token: await at.toJwt(),
  };
  return connectionDetails;
}
