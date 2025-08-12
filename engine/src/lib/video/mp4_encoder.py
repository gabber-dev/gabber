import asyncio
from core import runtime_types
import av
import numpy as np  # Assuming f.data is a numpy array; import if needed
import fractions
from queue import Queue
import threading
import io


class MP4_Encoder:
    def __init__(self):
        self.output = io.BytesIO()
        self.container = av.open(self.output, mode="w", format="mp4")
        self.video_stream = self.container.add_stream("libx264")
        self.encoder = self.video_stream.codec_context
        self.encoder.options = {"preset": "ultrafast", "crf": "0"}
        self.encoder.pix_fmt = "yuv444p"  # For minimal loss, preserving full chroma
        self.encoder.time_base = fractions.Fraction(1, 1000000)  # 1 microsecond units
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
                    self.container.mux(packet)
                break

            if self.encoder.width == 0 or self.encoder.height == 0:
                if not isinstance(f.data, np.ndarray):
                    raise ValueError("f.data must be a numpy ndarray")
                self.encoder.height, self.encoder.width = f.data.shape[:2]

            av_frame = av.VideoFrame.from_ndarray(f.data, format="rgba")
            av_frame.pts = int(round(f.timestamp / float(self.encoder.time_base)))
            packets = self.encoder.encode(av_frame)
            for p in packets:
                self.container.mux(p)

    async def eos(self):
        def wait_for_encode():
            self.input_queue.put(None)
            self.encode_thread.join()
            self.container.close()

        await asyncio.to_thread(wait_for_encode)

        return self.output.getvalue()
