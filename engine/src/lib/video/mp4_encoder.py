import asyncio
from core import runtime_types
import av
import numpy as np  # Assuming f.data is a numpy array; import if needed
import fractions
from queue import Queue
import threading


class MP4_Encoder:
    def __init__(self):
        self.encoder = av.CodecContext.create("libx264")
        self.encoder.options = {"preset": "ultrafast", "crf": "0"}
        self.encoder.pix_fmt = "yuv444p"  # For minimal loss, preserving full chroma
        self.encoder.time_base = fractions.Fraction(1, 1000000)  # 1 microsecond units
        self.packets: list[av.Packet] = []
        self.input_queue: Queue[runtime_types.VideoFrame | None] = Queue()
        self.encode_thread: threading.Thread = threading.Thread(
            target=self._encode_thread, daemon=True
        )

    def push_frames(self, frame: list[runtime_types.VideoFrame]):
        if not self.encode_thread.is_alive():
            self.encode_thread.start()
        for f in frame:
            self.input_queue.put(f)

    def _encode_thread(self):
        while True:
            f = self.input_queue.get()
            if f is None:
                packets = self.encoder.encode(None)
                for packet in packets:
                    self.packets.append(packet)
                break

            if self.encoder.width == 0 or self.encoder.height == 0:
                if not isinstance(f.data, np.ndarray):
                    raise ValueError("f.data must be a numpy ndarray")
                self.encoder.height, self.encoder.width = f.data.shape[:2]

            av_frame = av.VideoFrame.from_ndarray(f.data, format="rgba")
            av_frame.pts = int(round(f.timestamp / float(self.encoder.time_base)))
            packets = self.encoder.encode(av_frame)
            for p in packets:
                self.packets.append(p)

    async def eos(self):
        def wait_for_encode():
            self.input_queue.put(None)
            self.encode_thread.join()

        await asyncio.to_thread(wait_for_encode)

        res = b""

        for packet in self.packets:
            res += bytes(packet)

        return res
