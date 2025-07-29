/**
 * Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
 * SPDX-License-Identifier: SUL-1.0
 */

"use server";
import { getApp } from "@/lib/repository";
import {
  AccessToken,
  RoomServiceClient,
  AgentDispatchClient,
} from "livekit-server-sdk";
import { v4 as uuidv4 } from "uuid";

type CreateLivekitRoomParams = {
  appId: string;
};

type ConnectionDetails = {
  url: string;
  token: string;
};

export async function createLivekitRoom({
  appId,
}: CreateLivekitRoomParams): Promise<ConnectionDetails> {
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
  const appObj = await getApp(appId);

  await agentDispatchClient.createDispatch(roomName, "gabber-engine", {
    metadata: JSON.stringify({ app: appObj }),
  });
  const connectionDetails = {
    url: livekitUrl,
    token: await at.toJwt(),
  };
  return connectionDetails;
}
