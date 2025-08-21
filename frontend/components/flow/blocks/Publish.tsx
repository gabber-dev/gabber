/**
 * Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
 * SPDX-License-Identifier: SUL-1.0
 */

import { useEditor } from "@/hooks/useEditor";
import {
  LocalAudioTrack,
  LocalVideoTrack,
  useEngine,
} from "@gabber/client-react";
import {
  ComputerDesktopIcon,
  MicrophoneIcon,
  VideoCameraIcon,
} from "@heroicons/react/24/solid";
import { useNodeId } from "@xyflow/react";
import { useEffect, useRef, useState } from "react";
import toast from "react-hot-toast";

export function Publish() {
  const { debug } = useEditor();
  const { connectionState } = useEngine();
  const videoElRef = useRef<HTMLVideoElement>(null);

  if (debug) {
    return <div></div>;
  }

  return (
    <div className="flex flex-col w-full p-1">
      <div className="relative w-full aspect-video overflow-hidden">
        <div className="absolute z-10 right-2 bottom-2 h-[30px] w-1/3"></div>
        <video
          ref={videoElRef}
          className="absolute left-0 right-0 bottom-0 top-0 bg-black aspect-video"
        />
      </div>
      <Controls
        videoElRef={videoElRef}
        enabled={connectionState === "connected"}
      />
    </div>
  );
}

function Controls({
  videoElRef,
  enabled,
}: {
  videoElRef: React.RefObject<HTMLVideoElement | null>;
  enabled: boolean;
}) {
  const { publishToNode, getLocalTrack, connectionState } = useEngine();
  const nodeId = useNodeId();
  useEffect(() => {
    if (connectionState !== "disconnected") {
      setLocalMicrophoneTrack(null);
      setLocalWebcamTrack(null);
      setLocalScreenShareTrack(null);
    }
  }, [connectionState]);
  const [localWebcamTrack, setLocalWebcamTrack] =
    useState<LocalVideoTrack | null>(null);
  const [localMicrophoneTrack, setLocalMicrophoneTrack] =
    useState<LocalAudioTrack | null>(null);
  const [localScreenShareTrack, setLocalScreenShareTrack] =
    useState<LocalVideoTrack | null>(null);
  const [webcamPublication, setWebcamPublication] =
    useState<Publication | null>(null);
  return (
    <div className="flex items-center justify-center gap-2 p-2">
      <button
        className="rounded-full h-8 w-8 p-1.5 btn-primary btn text-primary-content relative"
        disabled={!enabled}
        onClick={async () => {
          if (!nodeId) {
            toast.error("Node ID is not available.");
            return;
          }
          if (localWebcamTrack) {
            setLocalWebcamTrack(null);
            return;
          }
          const webcamTrack = (await getLocalTrack({
            type: "webcam",
          })) as LocalVideoTrack;
          webcamTrack.attachToElement(videoElRef.current!);
          setLocalWebcamTrack(webcamTrack);
          const pub = await publishToNode({
            localTrack: webcamTrack,
            publishNodeId: nodeId,
          });
          setWebcamPublication(pub);
        }}
      >
        <VideoCameraIcon className="w-full h-full" />
        <div
          className={`absolute bottom-0 right-0 w-2 h-2 rounded-full ${localWebcamTrack ? "bg-red-500 animate-pulse" : "bg-gray-500"} ${enabled ? "" : "opacity-50"}`}
        ></div>
      </button>
      <button
        className="rounded-full h-8 w-8 p-1.5 btn-primary btn text-primary-content relative"
        disabled={!enabled}
        onClick={async () => {
          if (!nodeId) {
            toast.error("Node ID is not available.");
            return;
          }
          if (localMicrophoneTrack) {
            setLocalMicrophoneTrack(null);
            return;
          }
          const microphoneTrack = (await getLocalTrack({
            type: "microphone",
          })) as LocalAudioTrack;
          setLocalMicrophoneTrack(microphoneTrack);
          await publishToNode({
            localTrack: microphoneTrack,
            publishNodeId: nodeId,
          });
        }}
      >
        <MicrophoneIcon className="w-full h-full" />
        <div
          className={`absolute bottom-0 right-0 w-2 h-2 rounded-full ${localMicrophoneTrack ? "bg-red-500 animate-pulse" : "bg-gray-500"} ${enabled ? "" : "opacity-50"}`}
        ></div>
      </button>
      <button
        className="rounded-full h-8 w-8 p-1.5 btn-primary btn text-primary-content relative"
        disabled={!enabled}
        onClick={async () => {
          if (!nodeId) {
            toast.error("Node ID is not available.");
            return;
          }
          if (localScreenShareTrack) {
            setLocalScreenShareTrack(null);
            return;
          }
          try {
            const screenShareTrack = (await getLocalTrack({
              type: "screen",
              audio: false,
            })) as LocalVideoTrack;
            screenShareTrack.attachToElement(videoElRef.current!);
            setLocalScreenShareTrack(screenShareTrack);
            await publishToNode({
              localTrack: screenShareTrack,
              publishNodeId: nodeId,
            });
          } catch (error) {
            if (error instanceof Error) {
              if (
                error.name === "NotAllowedError" ||
                error.name === "PermissionDeniedError"
              ) {
                toast.error(
                  "Screen sharing permission was denied. Please allow screen sharing to continue.",
                );
              } else {
                toast.error(
                  "Failed to start screen sharing. Please try again.",
                );
              }
            } else {
              toast.error(
                "An unexpected error occurred while starting screen sharing.",
              );
            }
          }
        }}
      >
        <ComputerDesktopIcon className="w-full h-full" />
        <div
          className={`absolute bottom-0 right-0 w-2 h-2 rounded-full ${localScreenShareTrack ? "bg-red-500 animate-pulse" : "bg-gray-500"} ${enabled ? "" : "opacity-50"}`}
        ></div>
      </button>
    </div>
  );
}
