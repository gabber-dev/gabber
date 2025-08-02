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

import { Room } from 'livekit-client';
import { PropertySinkPad, PropertySourcePad, SinkPad, SourcePad } from './pad/Pad';
import { LocalAudioTrack, LocalVideoTrack, LocalTrack } from './LocalTrack';
import { Subscription } from './Subscription';
import { Value1 as PadTriggeredValue } from './generated/runtime';
import { Publication } from './Publication';

export interface EngineHandler {
  onConnectionStateChange?: (state: ConnectionState) => void;
}

export class Engine  {
  private livekitRoom: Room;
  private handler?: EngineHandler;
  private lastEmittedConnectionState: ConnectionState = "disconnected";

  constructor(params: {handler?: EngineHandler}) {
    this.livekitRoom = new Room();
    this.handler = params.handler;
    this.setupRoomEventListeners();
  }

  public get connectionState(): ConnectionState {
    if(this.livekitRoom.state === "connected") {
      const agentParticipants = Array.from(this.livekitRoom.remoteParticipants.values().filter(p => p.isAgent));
      if (agentParticipants.length > 0) {
        return 'connected';
      } else {
        return 'waiting_for_engine';
      }
    }

    if (this.livekitRoom.state === "connecting" || this.livekitRoom.state === "reconnecting") {
      return 'connecting';
    }
    return 'disconnected';
  }

  private emitConnectionStateChange(): void {
    if (this.handler?.onConnectionStateChange) {
      if (this.lastEmittedConnectionState === this.connectionState) {
        return; // No change, do not emit
      }
      this.lastEmittedConnectionState = this.connectionState;
      this.handler.onConnectionStateChange(this.lastEmittedConnectionState);
    }
  }

  public async connect(connectionDetails: ConnectionDetails): Promise<void> {
    await this.livekitRoom.connect(connectionDetails.url, connectionDetails.token);
  }

  public async disconnect(): Promise<void> {
    await this.livekitRoom.disconnect();
  }

  public async getLocalTrack(options: GetLocalTrackOptions): Promise<LocalTrack> {
    if(options.type === "microphone") {
      const mediaStream = await window.navigator.mediaDevices.getUserMedia({ audio: {
        echoCancellation: options.echoCancellation || true,
        noiseSuppression: options.noiseSuppression || true
      } })
      return new LocalAudioTrack({mediaStream});
    } else if(options.type === "webcam") {
      const mediaStream = await window.navigator.mediaDevices.getUserMedia({ video: {
        width: options.width || 640,
        height: options.height || 480,
        frameRate: options.fps || 30
      } });
      return new LocalVideoTrack({ mediaStream });
    } else if(options.type === "screen") {
      const mediaStream = await window.navigator.mediaDevices.getDisplayMedia({ video: true, audio: options.audio });
      return new LocalVideoTrack({ mediaStream });
    }

    throw new Error(`Unsupported track type`);
  }

  public async publishToNode(params: PublishParams): Promise<Publication> {
    if(params.localTrack.type === 'audio') {
      const track = params.localTrack as LocalAudioTrack;
      const mediaStreamTrack = track.mediaStream.getAudioTracks()[0];
      if (!mediaStreamTrack) {
        throw new Error('No audio track available to publish.');
      }
      const trackName = params.publishNodeId + ":audio";
      await this.livekitRoom.localParticipant.publishTrack(mediaStreamTrack, {name: trackName});
      return new Publication({ nodeId: params.publishNodeId, livekitRoom: this.livekitRoom, trackName });
    } else if (params.localTrack.type === 'video') {
      const track = params.localTrack as LocalVideoTrack;
      const mediaStreamTrack = track.mediaStream.getVideoTracks()[0];
      if (!mediaStreamTrack) {
        throw new Error('No video track available to publish.');
      }
      const trackName = params.publishNodeId + ":video";
      await this.livekitRoom.localParticipant.publishTrack(mediaStreamTrack, {name: trackName});
      return new Publication({ nodeId: params.publishNodeId, livekitRoom: this.livekitRoom, trackName });
    }
    throw new Error(`Unsupported track type: ${params.localTrack.type}`);
  }

  public async subscribeToNode(params: SubscribeParams): Promise<Subscription> {
    return new Subscription({nodeId: params.outputNodeId, livekitRoom: this.livekitRoom});
  }

  public getSourcePad<DataType extends PadTriggeredValue>(nodeId: string, padId: string): SourcePad<DataType> {
    return new SourcePad<DataType>({ nodeId, padId, livekitRoom: this.livekitRoom });
  }

  public getSinkPad<DataType extends PadTriggeredValue>(nodeId: string, padId: string): SinkPad<DataType> {
    return new SinkPad<DataType>({ nodeId, padId, livekitRoom: this.livekitRoom });
  }

  public getPropertySourcePad<DataType extends PadTriggeredValue>(nodeId: string, padId: string): SourcePad<DataType> {
    return new PropertySourcePad<DataType>({ nodeId, padId, livekitRoom: this.livekitRoom });
  }

  public getPropertySinkPad<DataType extends PadTriggeredValue>(nodeId: string, padId: string): SinkPad<DataType> {
    return new PropertySinkPad<DataType>({ nodeId, padId, livekitRoom: this.livekitRoom });
  }

  private setupRoomEventListeners(): void {
    this.livekitRoom.on('connected', () => {
      this.emitConnectionStateChange();
    });

    this.livekitRoom.on('disconnected', (reason) => {
      this.emitConnectionStateChange();
    });

    this.livekitRoom.on('participantConnected', (participant) => {
      this.emitConnectionStateChange();
    });

    this.livekitRoom.on('participantDisconnected', (participant) => {
      this.emitConnectionStateChange();
    });
  }
}

export type GetLocalTrackOptions_Webcam = {
  type: 'webcam';
  width?: number;
  height?: number;
  fps?: number;
}

export type GetLocalTrackOptions_Screen = {
  type: 'screen';
  audio: boolean;
}

export type GetLocalTrackOptions_Microphone = {
  type: 'microphone';
  echoCancellation?: boolean;
  noiseSuppression?: boolean;
}

export type GetLocalTrackOptions = GetLocalTrackOptions_Webcam | GetLocalTrackOptions_Screen | GetLocalTrackOptions_Microphone;


export type ConnectionDetails = {
  token: string;
  url: string;
}

export type PublishParams = {
  localTrack: LocalTrack;
  publishNodeId: string;
}

export type SubscribeParams = {
  outputNodeId: string;
}

export type ConnectionState = 'disconnected' | 'connecting' | 'waiting_for_engine' | 'connected';