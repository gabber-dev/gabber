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