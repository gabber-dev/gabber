import asyncio
from media import (
    VirtualCamera,
    VirtualMicrophone,
    MediaIterator,
    VideoFrame,
    AudioFrame,
)
from typing import cast
from livekit import rtc
import logging


class Publication:
    def __init__(
        self,
        *,
        node_id: str,
        livekit_room: rtc.Room,
        track_name: str,
        device: VirtualCamera | VirtualMicrophone,
    ):
        self.node_id = node_id
        self.livekit_room = livekit_room
        self.track_name = track_name
        self.device = device
        self._run_task: asyncio.Task | None = None
        self._publication: rtc.LocalTrackPublication | None = None

    async def start(self):
        iterator = self.device.create_iterator()

        def on_local_track_published(publication: rtc.LocalTrackPublication) -> None:
            if publication.name == self.track_name:
                logging.info(f"Published local video track: {publication.sid}")
            iterator.cleanup()

        self.livekit_room.on("track_published", on_local_track_published)

        try:
            local_track: rtc.LocalTrack
            if isinstance(self.device, VirtualCamera):
                source = rtc.VideoSource(
                    width=self.device.width, height=self.device.height
                )
                local_track = rtc.LocalVideoTrack.create_video_track(
                    self.track_name, source=source
                )
                self._publication = (
                    await self.livekit_room.local_participant.publish_track(local_track)
                )
                self._run_task = asyncio.create_task(
                    self._run_video(cast(MediaIterator[VideoFrame], iterator), source)
                )
            elif isinstance(self.device, VirtualMicrophone):
                source = rtc.AudioSource(
                    sample_rate=self.device.sample_rate,
                    num_channels=self.device.channels,
                )
                local_track = rtc.LocalAudioTrack.create_audio_track(
                    self.track_name, source=source
                )
                self._publication = (
                    await self.livekit_room.local_participant.publish_track(local_track)
                )
                self._run_task = asyncio.create_task(
                    self._run_audio(cast(MediaIterator[AudioFrame], iterator), source)
                )

        except Exception as e:
            logging.error(f"Error publishing track: {e}", exc_info=True)
            iterator.cleanup()

        self.livekit_room.off("track_published", on_local_track_published)

    async def _run_video(
        self, iterator: MediaIterator[VideoFrame], source: rtc.VideoSource
    ):
        try:
            async for item in iterator:
                lk_frame = item.to_livekit_video_frame()
                source.capture_frame(lk_frame)
        except Exception as e:
            logging.error(f"Error in video capture loop: {e}", exc_info=True)
        except asyncio.CancelledError:
            logging.info("Video capture task cancelled")

        if (
            self._publication
            and self._publication.track
            and self._publication.track.name
        ):
            await self.livekit_room.local_participant.unpublish_track(
                self._publication.track.name
            )

    async def _run_audio(
        self, iterator: MediaIterator[AudioFrame], source: rtc.AudioSource
    ):
        try:
            async for item in iterator:
                lk_frame = item.to_livekit_audio_frame()
                await source.capture_frame(lk_frame)
        except Exception as e:
            logging.error(f"Error in audio capture loop: {e}", exc_info=True)
        except asyncio.CancelledError:
            logging.info("Audio capture task cancelled")

        if (
            self._publication
            and self._publication.track
            and self._publication.track.name
        ):
            await self.livekit_room.local_participant.unpublish_track(
                self._publication.track.name
            )

    async def unpublish(self) -> None:
        if self._run_task:
            self._run_task.cancel()
            try:
                await self._run_task
            except asyncio.CancelledError:
                pass
            self._run_task = None

            if self._publication and self._publication.track:
                await self.livekit_room.local_participant.unpublish_track(
                    self._publication.track.name
                )
                self._publication = None
