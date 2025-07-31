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

import { Room } from "livekit-client";

type SinkPadParams = {
    nodeId: string;
    padId: string;
    livekitRoom: Room;
}

export class SourcePad<DataType> {
    private data: DataType | null = null;
    private handlers: Array<(data: DataType) => void> = [];
    private _nodeId: string;
    private _padId: string;
    private livekitRoom: Room;

    constructor({ nodeId, padId, livekitRoom }: SinkPadParams) {
        this._nodeId = nodeId;
        this._padId = padId;
        this.livekitRoom = livekitRoom;
    }

    public get nodeId(): string {
        return this._nodeId;
    }

    private set nodeId(value: string) {
        this._nodeId = value;
    }

    public get padId(): string {
        return this._padId;
    }

    private set padId(value: string) {
        this._padId = value;
    }
}