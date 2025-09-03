/**
 * Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
 * SPDX-License-Identifier: SUL-1.0
 */

import { useEngine } from "@gabber/client-react";
import { useNodeId } from "@xyflow/react";
import { useCallback, useEffect, useRef } from "react";

export function Output() {
  const { subscribeToNode, connectionState } = useEngine();
  const nodeId = useNodeId();
  const videoRef = useRef<HTMLVideoElement>(null);
  const audioRef = useRef<HTMLAudioElement>(null);
  const subscribed = useRef(false);

  const subscribe = useCallback(async () => {
    if (!nodeId) {
      console.error("Node ID is not available.");
      return;
    }
    if (subscribed.current) {
      console.warn("Already subscribed to node:", nodeId);
      return;
    }
    subscribed.current = true;
    const subscription = await subscribeToNode({
      outputOrPublishNodeId: nodeId,
    });
    subscription.waitForAudioTrack().then((track) => {
      track.attachToElement(audioRef.current!);
      audioRef.current!.play();
    });
    subscription.waitForVideoTrack().then((track) => {
      track.attachToElement(videoRef.current!);
    });
  }, [nodeId, subscribeToNode]);

  useEffect(() => {
    if (connectionState !== "connected") {
      subscribed.current = false;
      return;
    }
    subscribe();
  }, [connectionState, subscribe]);

  return (
    <div className="flex flex-col w-full p-1">
      <div className="relative w-full aspect-video overflow-hidden">
        <div className="absolute z-10 right-2 bottom-2 h-[30px] w-1/3"></div>
        <video
          ref={videoRef}
          className="absolute left-0 right-0 bottom-0 top-0 bg-black aspect-video"
        />
        <audio ref={audioRef} className="hidden" />
      </div>
    </div>
  );
}
