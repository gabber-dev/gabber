/**
 * Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
 * SPDX-License-Identifier: SUL-1.0
 */

import { MicrophoneIcon, VideoCameraIcon } from "@heroicons/react/24/solid";
import { useRealtimeSessionEngine } from "gabber-client-react";
import { useEffect, useMemo, useRef } from "react";

export function Publish() {
  const {
    webcamState,
    microphoneEnabled,
    setWebcamEnabled,
    setMicrophoneEnabled,
    innerEngine,
  } = useRealtimeSessionEngine();
  const cameraEnabled = webcamState === "on" || webcamState === "preview";

  return (
    <div className="flex flex-col w-full p-1">
      <div className="relative w-full aspect-video overflow-hidden">
        <div className="absolute z-10 right-2 bottom-2 h-[30px] w-1/3"></div>
        <video
          ref={(ref) => {
            if (!ref) return;
            innerEngine.setWebcamTrackDestination({ element: ref });
          }}
          id="gabber-webcam-track"
          className="absolute left-0 right-0 bottom-0 top-0 bg-black aspect-video"
        />
      </div>
      <div className="flex items-center justify-center gap-2 p-2">
        <button
          className={`rounded-full h-8 w-8 p-1.5 btn-primary btn text-primary-content relative ${
            cameraEnabled ? "border-2 border-primary border-opacity-50" : ""
          }`}
          onClick={() => setWebcamEnabled("on")}
        >
          <VideoCameraIcon className="w-full h-full" />
        </button>
        <button
          className={`rounded-full h-8 w-8 p-1.5 btn-primary btn text-primary-content relative ${
            microphoneEnabled ? "border-2 border-primary border-opacity-50" : ""
          }`}
          onClick={() => setMicrophoneEnabled(!microphoneEnabled)}
        >
          <MicrophoneIcon className="w-full h-full" />
        </button>
      </div>
    </div>
  );
}
