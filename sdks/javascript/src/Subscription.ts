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

import { RemoteAudioTrack as LKRemoteAudioTrack, RemoteVideoTrack as LKRemoteVideoTrack, RemoteTrack as LKRemoteTrack, Room, RemoteTrackPublication } from "livekit-client";
import { RemoteAudioTrack, RemoteVideoTrack } from "./RemoteTrack";

export class Subscription {
    private room: Room;
    private _nodeId: string;
    private audioCallbacks: {[key: string]: ((track: RemoteAudioTrack) => void)[]} = {};
    private videoCallbacks: {[key: string]: ((track: RemoteVideoTrack) => void)[]} = {};

    constructor(params: {nodeId: string, livekitRoom: Room}) {
        this.room = params.livekitRoom;
        this._nodeId = params.nodeId;
        this.waitForAudioTrack = this.waitForAudioTrack.bind(this);
        this.waitForVideoTrack = this.waitForVideoTrack.bind(this);
        this.onTrackSubscribed = this.onTrackSubscribed.bind(this);
        this.getExistingRemoteTracks = this.getExistingRemoteTracks.bind(this);
        this.subscribeToPublications = this.subscribeToPublications.bind(this);
        this.getExistingPublications = this.getExistingPublications.bind(this);
        this.onTrackPublished = this.onTrackPublished.bind(this);
        this.room.on('trackSubscribed', this.onTrackSubscribed);
        this.room.on('trackPublished', this.onTrackPublished);
    }

    public get nodeId(): string {
        return this._nodeId;
    }

    async waitForAudioTrack(): Promise<RemoteAudioTrack> {
        this.subscribeToPublications();
        const existingTracks = this.getExistingRemoteTracks('audio');
        if (existingTracks.length > 0) {
            return new RemoteAudioTrack({track: existingTracks[0] as LKRemoteAudioTrack});
        }
        const prom = new Promise<RemoteAudioTrack>((resolve, reject) => {
            if(!this.audioCallbacks[this._nodeId]) {
                this.audioCallbacks[this._nodeId] = [];
            }
            this.audioCallbacks[this._nodeId].push(resolve);
        });
        return prom;
    }

    async waitForVideoTrack(): Promise<RemoteVideoTrack> {
        this.subscribeToPublications();
        const existingTracks = this.getExistingRemoteTracks('video');
        if (existingTracks.length > 0) {
            return new RemoteVideoTrack({track: existingTracks[0] as LKRemoteVideoTrack});
        }
        const prom = new Promise<RemoteVideoTrack>((resolve, reject) => {
            if(!this.videoCallbacks[this._nodeId]) {
                this.videoCallbacks[this._nodeId] = [];
            }
            this.videoCallbacks[this._nodeId].push(resolve);
        });
        return prom;
    }

    private onTrackPublished(track: RemoteTrackPublication): void {
        console.log(`NEIL Track published`, track);
        if(track.trackName.startsWith(this._nodeId)) {
            track.setSubscribed(true);
        }
    }

    private onTrackSubscribed(track: LKRemoteTrack): void {
        console.log(`NEIL Track subscribed`, track);
        if(track.kind === 'audio') {
            const lkAudioTrack = track as LKRemoteAudioTrack;
            const res = new RemoteAudioTrack({track: lkAudioTrack});
            const callbacks = this.audioCallbacks[this._nodeId];
            if(callbacks) {
                callbacks.forEach(callback => callback(res));
                delete this.audioCallbacks[this._nodeId];
            }
        } else if(track.kind === 'video') {
            const lkVideoTrack = track as LKRemoteVideoTrack;
            const res = new RemoteVideoTrack({track: lkVideoTrack});
            const callbacks = this.videoCallbacks[this._nodeId];
            if(callbacks) {
                callbacks.forEach(callback => callback(res));
                delete this.videoCallbacks[this._nodeId];
            }
        }
    }

    private subscribeToPublications(): void {
        for (const publication of this.getExistingPublications()) {
            publication.setSubscribed(true);
        }
    }

    private getExistingPublications(): RemoteTrackPublication[] {
        const allPublications = Array.from(this.room.remoteParticipants.values())
            .flatMap(participant => participant.getTrackPublications())
            .filter(publication => publication.trackName.startsWith(this._nodeId));
        return allPublications as RemoteTrackPublication[];
    }

    private getExistingRemoteTracks(kind: "audio" | "video"): LKRemoteTrack[] {
        const allTracks = Array.from(this.room.remoteParticipants.values())
            .flatMap(participant => participant.getTrackPublications())
            .filter(track => track.trackName.startsWith(this._nodeId) && track.kind === kind).map(track => track.track);

        const res: LKRemoteTrack[] = [];
        for(const track of allTracks) {
            if(!track) {
                continue;
            }

            if(track.kind === 'audio') {
                res.push(track as LKRemoteAudioTrack);
            } else if(track.kind === 'video') {
                res.push(track as LKRemoteVideoTrack);
            }
        }
        return res;
    }
}