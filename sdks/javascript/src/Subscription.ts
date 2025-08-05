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

type AudioResolve = (track: RemoteAudioTrack) => void;
type VideoResolve = (track: RemoteVideoTrack) => void;
type Reject = (error: string) => void;

export class Subscription {
    private room: Room;
    private _nodeId: string;
    private audioCallbacks: {resolve: AudioResolve, reject: Reject}[] = [];
    private videoCallbacks: {resolve: VideoResolve, reject: Reject}[] = [];
    private publications: RemoteTrackPublication[] = [];

    constructor(params: {nodeId: string, livekitRoom: Room}) {
        this.room = params.livekitRoom;
        this._nodeId = params.nodeId;
        this.checkTrackSid = this.checkTrackSid.bind(this);
        this.waitForAudioTrack = this.waitForAudioTrack.bind(this);
        this.waitForVideoTrack = this.waitForVideoTrack.bind(this);
        this.onTrackSubscribed = this.onTrackSubscribed.bind(this);
        this.getExistingRemoteTracks = this.getExistingRemoteTracks.bind(this);
        this.subscribeToPublications = this.subscribeToPublications.bind(this);
        this.getExistingPublications = this.getExistingPublications.bind(this);
        this.onTrackPublished = this.onTrackPublished.bind(this);
        this.onDisconnected = this.onDisconnected.bind(this);
        this.cleanup = this.cleanup.bind(this);
        this.room.on('trackSubscribed', this.onTrackSubscribed);
        this.room.on('trackPublished', this.onTrackPublished);
        this.room.on('disconnected', this.onDisconnected);
    }

    public get nodeId(): string {
        return this._nodeId;
    }

    cleanup(): void {
        for(const publication of this.publications) {
            publication.setSubscribed(false);
        }
        this.publications = [];
        this.room.off('trackSubscribed', this.onTrackSubscribed);
        this.room.off('trackPublished', this.onTrackPublished);
        this.audioCallbacks.forEach(callback => callback.reject("Subscription cleaned up"));
        this.videoCallbacks.forEach(callback => callback.reject("Subscription cleaned up"));
        this.audioCallbacks = [];
        this.videoCallbacks = [];
    }

    async waitForAudioTrack(): Promise<RemoteAudioTrack> {
        this.subscribeToPublications();
        const existingTracks = this.getExistingRemoteTracks('audio');
        if (existingTracks.length > 0) {
            return new RemoteAudioTrack({track: existingTracks[0] as LKRemoteAudioTrack});
        }
        const prom = new Promise<RemoteAudioTrack>((resolve, reject) => {
            this.audioCallbacks.push({resolve, reject});
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
            this.videoCallbacks.push({resolve, reject});
        });
        return prom;
    }

    private onTrackPublished(track: RemoteTrackPublication): void {
        if(track.trackName.startsWith(this._nodeId)) {
            this.publications.push(track);
            track.setSubscribed(true);
        }
    }

    private onTrackSubscribed(track: LKRemoteTrack): void {
        if(!this.checkTrackSid(track)) {
            return;
        }
        if(track.kind === 'audio') {
            const lkAudioTrack = track as LKRemoteAudioTrack;
            const res = new RemoteAudioTrack({track: lkAudioTrack});
            this.audioCallbacks.forEach(callback => callback.resolve(res));
            this.audioCallbacks = [];
        } else if(track.kind === 'video') {
            const lkVideoTrack = track as LKRemoteVideoTrack;
            const res = new RemoteVideoTrack({track: lkVideoTrack});
            this.videoCallbacks.forEach(callback => callback.resolve(res));
            this.videoCallbacks = [];
        } else {
            console.warn("Received unsupported track type:", track.kind);
        }
    }

    private onDisconnected(): void {
        this.cleanup();
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

    private checkTrackSid(track: LKRemoteTrack): boolean {
        if(!track.sid) {
            console.warn("Track does not have a valid SID:", track);
            return false;
        }
        const allPublications = this.getExistingPublications();
        for(const publication of allPublications) {
            if(publication.trackSid === track.sid) {
                return true;
            }
        }
        return false;
    }
}