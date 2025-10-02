import logging

from engine import Engine
from lib import eot, stt, vad
from server import WebSocketServer, messages

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    def engine_factory(request: messages.RequestPayload_StartSession) -> Engine:
        return Engine(
            input_sample_rate=request.sample_rate,
            eot=eot.pipecat.PipeCatEOT(),
            vad=vad.VAD(vad_inference=vad.silero.SileroVADInference()),
            stt=stt.canary.CanarySTT(),
        )

    server = WebSocketServer(engine_factory=engine_factory)
    server.run()
