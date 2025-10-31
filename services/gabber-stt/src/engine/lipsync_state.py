from typing import Generic, TypeVar, TYPE_CHECKING
import logging
from lib.lipsync import LipSyncResult, VisemeProability, Viseme

if TYPE_CHECKING:
    from .engine import Engine
from dataclasses import dataclass, field

T = TypeVar("T")


class BaseLipSyncState(Generic[T]):
    def __init__(self, *, engine: "Engine", state: T):
        self.name = self.__class__.__name__.split("_")[-1]
        self.engine = engine
        self.state = state

    async def tick(self): ...

    def lipsync_to_input_curs(self, lipsync_curs: int) -> int:
        return self.engine.audio_window.convert_cursor(
            from_rate=self.engine.lipsync.sample_rate,
            to_rate=self.engine._input_sample_rate,
            cursor=lipsync_curs,
        )

    async def lipsync_results(
        self, start_curs: int, end_curs: int
    ) -> "list[list[LipSyncResult]]":
        results: list[list[LipSyncResult]] = []
        for i in range(
            start_curs,
            end_curs,
            self.engine.lipsync.inference_impl.new_audio_size,
        ):
            segment_end = min(
                i + self.engine.lipsync.inference_impl.full_audio_size, end_curs
            )
            if segment_end - i < self.engine.lipsync.inference_impl.full_audio_size:
                break

            segment = self.engine.audio_window.get_segment(
                sample_rate=self.engine.lipsync.sample_rate,
                start_curs=i,
                ends_curs=segment_end,
            )
            res = await self.engine.lipsync.simple_inference(segment)
            # offset_samples
            for r in res:
                r.start_sample += i
                r.end_sample += i
            results.append(res)
        return results

    @property
    def latest_lipsync_cursor(self):
        return self.engine.audio_window._end_cursors.get(
            self.engine.lipsync.sample_rate, 0
        )


@dataclass
class ListeningState:
    commit_cursor: int = 0
    last_emit: int = 0
    last_emitted_viseme: Viseme = Viseme.SILENCE
    last_emitted_viseme_end: int = 0


class LipSyncState_Listening(BaseLipSyncState[ListeningState]):
    async def tick(self):
        start = (
            self.latest_lipsync_cursor
            - self.engine.lipsync.inference_impl.full_audio_size
        )
        results: list[list[LipSyncResult]] = await self.lipsync_results(
            start, self.latest_lipsync_cursor
        )
        time_since_commit = (
            self.latest_lipsync_cursor - self.state.commit_cursor
        ) / self.engine.lipsync.sample_rate

        if time_since_commit < self.engine.settings.lipsync_delay_s:
            return

        if len(results) == 0:
            return

        latest_result = results[-1]

        for r in latest_result:
            # Ignore already committed visemes
            if r.end_sample <= self.state.commit_cursor:
                continue

            # Ignore visemes that are too new
            if (
                r.end_sample
                > self.latest_lipsync_cursor
                - self.engine.settings.lipsync_delay_s * self.engine.lipsync.sample_rate
            ):
                continue

            # commit viseme
            start_sample = r.start_sample
            if r.start_sample > self.state.commit_cursor:
                logging.warning("LipSyncState_Listening - start_sample > commit_cursor")
                start_sample = self.state.commit_cursor

            time_since_emit = (
                r.end_sample - self.state.last_emit
            ) / self.engine.lipsync.sample_rate
            if (
                time_since_emit > 0.25
                or r.max_viseme_prob.viseme != self.state.last_emitted_viseme
            ):
                start = min(self.state.last_emitted_viseme_end, start_sample)
                self.engine._on_event(
                    LipSyncEvent_Viseme(
                        viseme=r.max_viseme_prob.viseme,
                        probability=r.max_viseme_prob.probability,
                        start_sample=self.lipsync_to_input_curs(start),
                        end_sample=self.lipsync_to_input_curs(r.end_sample),
                    )
                )
                self.state.last_emit = r.end_sample
                self.state.last_emitted_viseme = r.max_viseme_prob.viseme
                self.state.last_emitted_viseme_end = r.end_sample
            self.state.commit_cursor = r.end_sample


@dataclass
class LipSyncEvent_Viseme:
    viseme: Viseme
    probability: float
    start_sample: int
    end_sample: int
