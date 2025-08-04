import { RemoteAudioTrack as LKRemoteAudioTrack, RemoteVideoTrack as LKRemoteVideoTrack, RemoteTrack as LKRemoteTrack, Room, RemoteTrackPublication } from "livekit-client";
import { RemoteAudioTrack, RemoteVideoTrack } from "./RemoteTrack";

export class Publication {
    private room: Room;
    private _nodeId: string;
    private trackName: string;

    constructor(params: {nodeId: string, livekitRoom: Room, trackName: string}) {
        this.room = params.livekitRoom;
        this._nodeId = params.nodeId;
        this.trackName = params.trackName;
    }

    public get nodeId(): string {
        return this._nodeId;
    }
}