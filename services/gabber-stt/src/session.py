from enum import Enum


class Session:
    pass


class TalkingState(Enum):
    SILENCE = 0
    SPEAKING = 1
    END_OF_TURN = 2


class SessionStateMachine:
    pass
