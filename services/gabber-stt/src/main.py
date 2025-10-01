import logging
from server import WebSocketServer

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    def engine_factory():
        from engine import Engine
        from lib import eot, vad, stt

        return Engine(
            eot=eot.EndOfTurn(),
            vad=vad.VAD(),
            stt=stt.STT(),
        )

    server = WebSocketServer(engine_factory=engine_factory)
    server.run()
