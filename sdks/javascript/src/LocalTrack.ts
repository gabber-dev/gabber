export class LocalTrack {
    constructor() {}

    public get type(): string {
        throw new Error("Method 'type' must be implemented.");
    }
}

export class LocalAudioTrack extends LocalTrack {
    public mediaStream: MediaStream;
    constructor(params: { mediaStream: MediaStream }) {
        super();
        this.mediaStream = params.mediaStream;
    }

    async attachToElement(element: HTMLAudioElement) {
        if(element.srcObject !== this.mediaStream) {
            element.srcObject = null; // Clear previous source
        }
        if (this.mediaStream) {
            element.srcObject = this.mediaStream;
            await element.play();
        } else {
            throw new Error('No audio track available to attach.');
        }
    }

    public get type(): string {
        return 'audio';
    }
}


export class LocalVideoTrack extends LocalTrack {
    public mediaStream: MediaStream;
    constructor(params: { mediaStream: MediaStream }) {
        super();
        this.mediaStream = params.mediaStream;
    }

    async attachToElement(element: HTMLVideoElement) {
        if(element.srcObject !== this.mediaStream) {
            element.srcObject = null; // Clear previous source
        }
        if (this.mediaStream) {
            element.srcObject = this.mediaStream;
            await element.play();
        } else {
            throw new Error('No video track available to attach.');
        }
    }

    public get type(): string {
        return 'video';
    }
}