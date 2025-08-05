/**
 * Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 *
 * SPDX-License-Identifier: Apache-2.0
 */

import { RemoteAudioTrack as LKRemoteAudioTrack, RemoteVideoTrack as LKRemoteVideoTrack, RemoteTrack as LKRemoteTrack, Room } from "livekit-client";

export class RemoteTrack {
    constructor() {}

    public get type(): "audio" | "video" {
        throw new Error("Method 'type' must be implemented.");
    }
}

export class RemoteAudioTrack extends RemoteTrack {
    private lkTrack: LKRemoteAudioTrack;

    constructor(params: {track: LKRemoteAudioTrack}) {
        super();
        this.lkTrack = params.track;
    }

    public get type(): "audio" {
        return 'audio';
    }

    attachToElement(element: HTMLMediaElement): void {
        this.lkTrack.attach(element);
    }

    detachFromElement(element: HTMLMediaElement): void {
        this.lkTrack.detach(element);
    }
}

export class RemoteVideoTrack extends RemoteTrack {
    private lkTrack: LKRemoteVideoTrack;

    constructor(params: {track: LKRemoteVideoTrack}) {
        super();
        this.lkTrack = params.track;
    }

    public get type(): "video" {
        return 'video';
    }

    attachToElement(element: HTMLVideoElement): void {
        this.lkTrack.attach(element);
    }

    detachFromElement(element: HTMLVideoElement): void {
        this.lkTrack.detach(element);
    }
}