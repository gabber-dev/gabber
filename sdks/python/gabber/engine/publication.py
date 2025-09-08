import asyncio
from media import VirtualCamera, VirtualMicrophone
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

    def _start(self):
        self._run_task = asyncio.create_task(self._run())

    async def _run(self):
        if isinstance(self.device, VirtualCamera):
            await self._run_video()
        elif isinstance(self.device, VirtualMicrophone):
            await self._run_audio()

    async def _run_video(self):
        assert isinstance(self.device, VirtualCamera)
        iterator = self.device.create_iterator()
        local_track: rtc.LocalVideoTrack
        source = rtc.VideoSource(width=self.device.width, height=self.device.height)
        local_track = rtc.LocalVideoTrack.create_video_track(
            self.track_name, source=source
        )

        def on_local_track_published(publication: rtc.LocalTrackPublication) -> None:
            if publication.name == self.track_name:
                logging.info(f"Published local video track: {publication.sid}")
            iterator.cleanup()

        self.livekit_room.on("local_track_unpublished", on_local_track_published)
        pub = await self.livekit_room.local_participant.publish_track(local_track)
        try:
            async for item in iterator:
                lk_frame = item.to_livekit_video_frame()
                source.capture_frame(lk_frame)
        except Exception as e:
            logging.error(f"Error in video capture loop: {e}", exc_info=True)
        except asyncio.CancelledError:
            logging.info("Video capture task cancelled")
            if pub.track:
                try:
                    await self.livekit_room.local_participant.unpublish_track(
                        pub.track.sid
                    )
                except Exception as e:
                    logging.error(f"Error unpublishing track: {e}", exc_info=True)
                    iterator.cleanup()

    async def _run_audio(self):
        assert isinstance(self.device, VirtualMicrophone)
        iterator = self.device.create_iterator()
        local_track: rtc.LocalAudioTrack
        source = rtc.AudioSource(
            sample_rate=self.device.sample_rate, num_channels=self.device.channels
        )
        local_track = rtc.LocalAudioTrack.create_audio_track(
            self.track_name, source=source
        )

        def on_local_track_published(publication: rtc.LocalTrackPublication) -> None:
            if publication.name == self.track_name:
                logging.info(f"Published local audio track: {publication.sid}")
            iterator.cleanup()

        self.livekit_room.on("local_track_unpublished", on_local_track_published)
        pub = await self.livekit_room.local_participant.publish_track(local_track)
        try:
            async for item in iterator:
                lk_frame = item.to_livekit_audio_frame()
                await source.capture_frame(lk_frame)
        except Exception as e:
            logging.error(f"Error in video capture loop: {e}", exc_info=True)
        except asyncio.CancelledError:
            logging.info("Video capture task cancelled")
            if pub.track:
                try:
                    await self.livekit_room.local_participant.unpublish_track(
                        pub.track.sid
                    )
                except Exception as e:
                    logging.error(f"Error unpublishing track: {e}", exc_info=True)
                    iterator.cleanup()

    async def unpublish(self) -> None:
        if self._run_task:
            self._run_task.cancel()
            try:
                await self._run_task
            except asyncio.CancelledError:
                pass
            self._run_task = None
