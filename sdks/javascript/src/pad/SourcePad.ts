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
import { RuntimeRequest, RuntimeRequestAck, RuntimeRequestComplete, RuntimeRequestPayload_PushValue } from "../generated/runtime"

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
    private requestIdCounter: number = 0;
    private pendingRequests: Map<string, {res: (response: any) => void, rej: (error: string) => void}> = new Map();

    constructor({ nodeId, padId, livekitRoom }: SinkPadParams) {
        this._nodeId = nodeId;
        this._padId = padId;
        this.livekitRoom = livekitRoom;
        this.get_request_id = this.get_request_id.bind(this);
        this.pushValue = this.pushValue.bind(this);
        this.onData = this.onData.bind(this);
        this.livekitRoom.on('dataReceived', this.onData);
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

    private get_request_id(): string {
        return this.nodeId + "_" + this.padId + "_" + this.requestIdCounter++;
    }

    public async pushValue(value: DataType): Promise<void> {
        this.data = value;
        this.handlers.forEach(handler => handler(value));

        const payload: RuntimeRequestPayload_PushValue = {
            type: "push_value",
            node_id: this.nodeId,
            source_pad_id: this.padId,
            value: (value as any)
        };
        const req_id = this.get_request_id();
        const request: RuntimeRequest = {
            type: "request",
            req_id: req_id,
            payload: payload
        };
        const requestJson = JSON.stringify(request);
        const requestBytes = new TextEncoder().encode(requestJson);
        const prom = new Promise<void>(async (res, rej) => {
            this.pendingRequests.set(req_id, {res, rej});
            await this.livekitRoom.localParticipant.publishData(requestBytes, {topic: "runtime"});
        });
        return prom;
    }

    private onData(data: Uint8Array): void {
        const msg = JSON.parse(new TextDecoder().decode(data));
        if (msg.type === "ack") {
            console.log("Received ACK for request:", msg.req_id);
        } else if (msg.type === "complete") {
            console.log("Received COMPLETE for request:", msg.req_id);
            if(msg.error) {
                console.error("Error in request:", msg.error);
                const pendingRequest = this.pendingRequests.get(msg.req_id);
                if (pendingRequest) {
                    pendingRequest.rej(msg.error);
                }
            } else {
                const pendingRequest = this.pendingRequests.get(msg.req_id);
                if (pendingRequest) {
                    pendingRequest.res(msg.payload);
                }
            }
            this.pendingRequests.delete(msg.req_id);
        } else if (msg.type === "event") {
            console.log("Received event:", msg.event);
        }
    }
}