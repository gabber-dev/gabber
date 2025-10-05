import logging

from engine import Engine
from lib import eot, stt, vad
from server import WebSocketServer, messages

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    def engine_factory(request: messages.RequestPayload_StartSession) -> Engine:
        return Engine(
            input_sample_rate=request.sample_rate,
            eot=eot.EndOfTurn(
                eot_inference=eot.pipecat.PipeCatEOTInference(), tick_s=0.4
            ),
            vad=vad.VAD(vad_inference=vad.silero.SileroVADInference()),
            stt=stt.STT(
                stt_inference=stt.parakeet.ParakeetSTTInference(
                    left_context_secs=15.0, right_context_secs=0.2, chunk_secs=0.2
                )
            ),
        )

    server = WebSocketServer(engine_factory=engine_factory)
    server.run()
