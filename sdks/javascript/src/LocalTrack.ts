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

export class LocalTrack {
    constructor() {}

    public get type(): string {
        throw new Error("Method 'type' must be implemented.");
    }
}

export class LocalAudioTrack extends LocalTrack {
    public mediaStream: MediaStream;
    constructor(params: { mediaStream: MediaStream }) {
        super();
        this.mediaStream = params.mediaStream;
    }

    async attachToElement(element: HTMLAudioElement) {
        if(element.srcObject !== this.mediaStream) {
            element.srcObject = null; // Clear previous source
        }
        if (this.mediaStream) {
            element.srcObject = this.mediaStream;
            await element.play();
        } else {
            throw new Error('No audio track available to attach.');
        }
    }

    public get type(): string {
        return 'audio';
    }
}


export class LocalVideoTrack extends LocalTrack {
    public mediaStream: MediaStream;
    constructor(params: { mediaStream: MediaStream }) {
        super();
        this.mediaStream = params.mediaStream;
    }

    async attachToElement(element: HTMLVideoElement) {
        if(element.srcObject !== this.mediaStream) {
            element.srcObject = null; // Clear previous source
        }
        if (this.mediaStream) {
            element.srcObject = this.mediaStream;
            await element.play();
        } else {
            throw new Error('No video track available to attach.');
        }
    }

    public get type(): string {
        return 'video';
    }
}