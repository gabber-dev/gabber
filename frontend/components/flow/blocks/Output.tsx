/**
 * Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
 * SPDX-License-Identifier: SUL-1.0
 */

export function Output() {
  return (
    <div className="flex flex-col w-full p-1">
      <div className="relative w-full aspect-video overflow-hidden">
        <div className="absolute z-10 right-2 bottom-2 h-[30px] w-1/3"></div>
        <video
          ref={(ref) => {
            if (!ref) return;
            // innerEngine.setVideoTrackDestination({ element: ref });
          }}
          id="gabber-webcam-track"
          className="absolute left-0 right-0 bottom-0 top-0 bg-black aspect-video"
        />
      </div>
    </div>
  );
}
