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
}