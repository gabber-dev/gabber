import asyncio
import logging

from engine import Engine, EngineSettings
from lib import eot, stt, vad, lipsync
from server import WebSocketServer, messages


async def main():
    eot_engine = eot.EndOfTurnEngine(inference_impl=eot.pipecat.PipeCatEOTInference())
    vad_engine = vad.VADInferenceEngine(inference_impl=vad.silero.SileroVADInference())
    stt_engine = stt.STTInferenceEngine(
        # inference_impl=stt.parakeet.ParakeetSTTInference(
        #     window_secs=120.0,  # There is a bug I can't find with the RNN continuation logic so for now we will just use a long window which is fine in practice for realtime conversational use cases.
        # )
        inference_impl=stt.mock.MockSTTInference(window_secs=20.0),
    )
    lipsync_engine = lipsync.LipSyncInferenceEngine(
        inference_impl=lipsync.OpenLipSyncInference()
    )

    await stt_engine.initialize()
    await eot_engine.initialize()
    await vad_engine.initialize()
    await lipsync_engine.initialize()

    def engine_factory(request: messages.RequestPayload_StartSession) -> Engine:
        settings = EngineSettings()
        settings.lipsync_enabled = request.lipsync_enabled
        settings.stt_enabled = request.stt_enabled
        return Engine(
            input_sample_rate=request.sample_rate,
            eot=eot_engine,
            vad=vad_engine,
            stt=stt_engine,
            lipsync=lipsync_engine,
            settings=settings,
        )

    server = WebSocketServer(engine_factory=engine_factory)
    await server.run()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
