import asyncio
import logging

from engine import Engine
from lib import eot, stt, vad
from server import WebSocketServer, messages


async def main():
    eot_engine = eot.EndOfTurnEngine(inference_impl=eot.pipecat.PipeCatEOTInference())
    vad_engine = vad.VADInferenceEngine(inference_impl=vad.silero.SileroVADInference())
    stt_engine = stt.STTInferenceEngine(
        inference_impl=stt.parakeet.ParakeetSTTInference(
            window_secs=20.0,
        )
        # inference_impl=stt.mock.MockSTTInference(window_secs=20.0),
    )

    await stt_engine.initialize()
    await eot_engine.initialize()
    await vad_engine.initialize()

    def engine_factory(request: messages.RequestPayload_StartSession) -> Engine:
        return Engine(
            input_sample_rate=request.sample_rate,
            eot=eot_engine,
            vad=vad_engine,
            stt=stt_engine,
        )

    server = WebSocketServer(engine_factory=engine_factory)
    await server.run()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
