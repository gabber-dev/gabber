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
import { PadValue, RuntimeRequest, RuntimeRequestPayload_PushValue } from "../generated/runtime"
import { Engine } from "../Engine";

type PadParams = {
    nodeId: string;
    padId: string;
    livekitRoom: Room;
    engine: Engine
}

export class BasePad<DataType extends PadValue> {
    protected handlers: Array<(data: DataType) => void> = [];
    private _nodeId: string;
    private _padId: string;
    protected livekitRoom: Room;
    private requestIdCounter: number = 0;
    protected engine: Engine;

    constructor({ nodeId, padId, livekitRoom, engine }: PadParams) {
        console.debug("Creating new BasePad instance for node", nodeId, "pad", padId);
        this.engine = engine;
        this._nodeId = nodeId;
        this._padId = padId;
        this.livekitRoom = livekitRoom;
        this.get_request_id = this.get_request_id.bind(this);
        this.destroy = this.destroy.bind(this);
    }

    public on(event: "value", handler: (data: DataType) => void): void {
        this.handlers.push(handler);
    }

    public off(event: "value", handler: (data: DataType) => void): void {
        this.handlers = this.handlers.filter(h => h !== handler);
    }

    public destroy(): void {
        console.debug("Destroying pad", this.nodeId, this.padId);
        this.handlers = [];
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

    protected async _getValue(): Promise<DataType> {
        const resp = await this.engine.runtimeRequest({
            payload: {
                type: "get_value",
                node_id: this.nodeId,
                pad_id: this.padId,
            },
            nodeId: this.nodeId,
            padId: this.padId
        });
        if(resp?.type !== "get_value") {
            throw new Error(`Unexpected response type: ${resp?.type}`);
        }
        if(resp.value === undefined) {
            throw new Error("No value in response");
        }
        return resp.value;
    }
}

export class SourcePad<DataType extends PadValue> extends BasePad<DataType> {
    constructor(params: PadParams) {
        super(params);
        this.pushValue = this.pushValue.bind(this);
    }

    public async pushValue(value: DataType): Promise<void> {
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

export class SinkPad<DataType extends PadValue> extends BasePad<DataType> {
    constructor(params: PadParams) {
        super(params);
    }
}

export class PropertyPad<DataType extends PadValue> extends BasePad<DataType> {
    constructor(params: PadParams) {
        super(params);
    }

    public async getValue(): Promise<DataType> {
        return this._getValue();
    }
}