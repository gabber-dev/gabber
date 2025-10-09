from core import AudioInferenceInternalResult, AudioInferenceRequest

from ..stt import STTInference, STTInferenceResult, STTInferenceResultWord


class MockSTTInference(STTInference):
    def __init__(
        self,
        *,
        window_secs: float = 10.0,
    ):
        self._window_sec = window_secs

    async def initialize(self) -> None:
        pass

    @property
    def sample_rate(self) -> int:
        return 16000

    @property
    def new_audio_size(self) -> int:
        return 1600 * 2

    @property
    def full_audio_size(self) -> int:
        return int(self._window_sec * self.sample_rate)

    def inference(
        self, input: AudioInferenceRequest
    ) -> list[AudioInferenceInternalResult[STTInferenceResult]]:
        if input.audio_batch.shape[1] != self.full_audio_size:
            raise ValueError(
                f"Invalid audio chunk size: {input.audio_batch.shape[1]}, expected {self.full_audio_size}"
            )

        batch_size = input.audio_batch.shape[0]
        results: list[AudioInferenceInternalResult[STTInferenceResult]] = []
        for _ in range(batch_size):
            words = [
                STTInferenceResultWord(
                    word="hello",
                    start_cursor=0,
                    end_cursor=10,
                ),
                STTInferenceResultWord(
                    word="world",
                    start_cursor=10,
                    end_cursor=20,
                ),
            ]
            transcription = "hello world"
            result = STTInferenceResult(
                transcription=transcription,
                start_cursor=0,
                end_cursor=20,
                words=words,
            )
            results.append(AudioInferenceInternalResult(result=result, state=None))
        return results
