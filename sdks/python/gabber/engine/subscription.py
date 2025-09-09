import asyncio
from typing import cast

import numpy as np
from livekit import rtc

from ..media import AudioFrame, MediaIterator, VideoFrame


class Subscription:
    def __init__(
        self,
        *,
        node_id: str,
        livekit_room: rtc.Room,
        track_name: str,
    ):
        self.node_id = node_id
        self.livekit_room = livekit_room
        self.track_name = track_name
        self._run_task: asyncio.Task | None = None
        self._run_task: asyncio.Task | None = None
        self._stream: rtc.AudioStream | rtc.VideoStream | None = None
        self._audio_iterators: list[MediaIterator[AudioFrame]] = []
        self._video_iterators: list[MediaIterator[VideoFrame]] = []

    async def start(self) -> None:
        self._run_task = asyncio.create_task(self._run())

    async def iterate_audio(self):
        new_it = MediaIterator[AudioFrame](owner=self)
        self._audio_iterators.append(new_it)

    async def iterate_video(self):
        new_it = MediaIterator[VideoFrame](owner=self)
        self._video_iterators.append(new_it)

    def unsubscribe(self) -> None:
        if self._run_task:
            self._run_task.cancel()
            self._run_task = None

    async def _run(self) -> None:
        pubs = await self._get_publications()
        tasks = [asyncio.create_task(self._run_publication(pub)) for pub in pubs]
        await asyncio.gather(*tasks)

    async def _run_publication(self, pub: rtc.RemoteTrackPublication) -> None:
        if not pub.subscribed:
            pub.set_subscribed(True)

        while True:
            await asyncio.sleep(0.2)
            track = pub.track
            if track is not None:
                await self._run_track(track)

    async def _run_track(self, track: rtc.RemoteTrack) -> None:
        if isinstance(track, rtc.AudioStream):
            stream = rtc.AudioStream(track)
            async for frame in stream:
                np_arr = np.frombuffer(frame.frame.data, dtype=np.int16)
                af = AudioFrame(
                    data=np_arr,
                    sample_rate=frame.frame.sample_rate,
                    num_channels=frame.frame.num_channels,
                )
                for it in self._audio_iterators:
                    it._push(af)
        elif isinstance(track, rtc.VideoStream):
            stream = rtc.VideoStream(track)
            async for frame in stream:
                np_arr = np.frombuffer(frame.frame.data, dtype=np.uint8)
                vf = VideoFrame(
                    data=np_arr,
                    width=frame.frame.width,
                    height=frame.frame.height,
                    format=VideoFrame.format,
                )
                for it in self._video_iterators:
                    it._push(vf)

    async def _get_publications(self):
        all_publications: list[rtc.RemoteTrackPublication] = []
        for part in self.livekit_room.remote_participants.values():
            for pub in part.track_publications.values():
                all_publications.append(pub)

        all_publications = [
            p for p in all_publications if p.name.startswith(f"{self.node_id}:")
        ]
        return all_publications

    async def _unsubscribe_all(self) -> None:
        pubs = await self._get_publications()
        for p in pubs:
            if p.subscribed:
                p.set_subscribed(False)

    def remove_iterator(self, iterator: MediaIterator) -> None:
        if iterator in self._video_iterators:
            self._video_iterators.remove(iterator)

        if iterator in self._audio_iterators:
            self._audio_iterators.remove(iterator)
