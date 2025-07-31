import { Room } from "livekit-client";

type SinkPadParams = {
    nodeId: string;
    padId: string;
    livekitRoom: Room;
}

export class SinkPad<DataType> {
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

    addHandler(h: (data: DataType) => void): void {
        this.handlers.push(h);
        if (this.data !== null) {
            h(this.data);
        }
    }

    removeHandler(h: (data: DataType) => void): void {
        const index = this.handlers.indexOf(h);
        if (index !== -1) {
            this.handlers.splice(index, 1);
        }
    }

    removeAllHandlers(): void {
        this.handlers = [];
    }
}