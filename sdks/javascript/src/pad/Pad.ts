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

import { DataPacket_Kind, RemoteParticipant, Room } from "livekit-client";
import { RuntimeRequest, RuntimeRequestAck, RuntimeRequestPayload_PushValue, RuntimeEvent, RuntimeEvent_PadTriggered, RuntimeRequestPayload_GetValue, RuntimeResponsePayload_GetValue } from "../generated/runtime"

type PadParams = {
    nodeId: string;
    padId: string;
    livekitRoom: Room;
}

export class BasePad<DataType> {
    protected handlers: Array<(data: DataType) => void> = [];
    private _nodeId: string;
    private _padId: string;
    protected livekitRoom: Room;
    private requestIdCounter: number = 0;
    protected pendingRequests: Map<string, {res: (response: any) => void, rej: (error: string) => void}> = new Map();
    protected channelTopic: string;

    constructor({ nodeId, padId, livekitRoom }: PadParams) {
        this._nodeId = nodeId;
        this._padId = padId;
        this.livekitRoom = livekitRoom;
        this.get_request_id = this.get_request_id.bind(this);
        this.onData = this.onData.bind(this);
        this.livekitRoom.on('dataReceived', this.onData);
        this.channelTopic = "runtime:" + this._nodeId + ":" + this._padId;
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

    protected get_request_id(): string {
        return this.nodeId + "_" + this.padId + "_" + this.requestIdCounter++;
    }

    private onData(data: Uint8Array, _: RemoteParticipant | undefined, __: DataPacket_Kind | undefined, topic: string | undefined): void {
        if (topic !== this.channelTopic) {
            return; // Ignore data not on this pad's channel
        }
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

    protected async _getValue(): Promise<DataType> {
        const payload: RuntimeRequestPayload_GetValue = {
            type: "get_value",
            node_id: this.nodeId,
            property_pad_id: this.padId,
        };
        const req_id = this.get_request_id();
        const request: RuntimeRequest = {
            type: "request",
            req_id: req_id,
            payload: payload
        };
        const requestJson = JSON.stringify(request);
        const requestBytes = new TextEncoder().encode(requestJson);
        const prom = new Promise<DataType>(async (res, rej) => {
            this.pendingRequests.set(req_id, {res, rej});
            await this.livekitRoom.localParticipant.publishData(requestBytes, {topic: this.channelTopic});
        });
        return prom;
    }
}

export class SourcePad<DataType> extends BasePad<DataType> {
    constructor(params: PadParams) {
        super(params);
        this.pushValue = this.pushValue.bind(this);
    }

    public async pushValue(value: DataType): Promise<void> {
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
            await this.livekitRoom.localParticipant.publishData(requestBytes, {topic: this.channelTopic});
        });
        return prom;
    }
}

export class SinkPad<DataType> extends BasePad<DataType> {
    constructor(params: PadParams) {
        super(params);
    }
}

export class PropertySourcePad<DataType> extends SourcePad<DataType> {
    constructor(params: PadParams) {
        super(params);
    }

    public async getValue(): Promise<DataType> {
        return this._getValue();
    }
}

export class PropertySinkPad<DataType> extends SinkPad<DataType> {
    constructor(params: PadParams) {
        super(params);
    
    }

    public async getValue(): Promise<DataType> {
        return this._getValue();
    }
}