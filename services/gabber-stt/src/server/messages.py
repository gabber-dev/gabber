from pydantic import BaseModel, Field
from typing import Literal, Annotated
from engine import (
    EngineEvent,
    STTEvent_FinalTranscription,
    STTEvent_InterimTranscription,
    STTEvent_SpeakingStarted,
    LipSyncEvent_Viseme,
)


class RequestPayload_StartSession(BaseModel):
    type: Literal["start_session"] = "start_session"
    sample_rate: int
    stt_enabled: bool = True
    lipsync_enabled: bool = False


class RequestPayload_AudioData(BaseModel):
    type: Literal["audio"] = "audio"
    b64_data: str


class RequestPayload_EndSession(BaseModel):
    type: Literal["end_session"] = "end_session"


RequestPayload = Annotated[
    RequestPayload_StartSession | RequestPayload_AudioData | RequestPayload_EndSession,
    Field(discriminator="type"),
]


class Request(BaseModel):
    payload: RequestPayload
    session_id: str


class ResponsePayload_Error(BaseModel):
    type: Literal["error"] = "error"
    message: str


class ResponsePayload_InterimTranscription(BaseModel):
    type: Literal["interim_transcription"] = "interim_transcription"
    trans_id: int
    start_sample: int
    end_sample: int
    transcription: str


class ResponsePayload_SpeakingStarted(BaseModel):
    type: Literal["speaking_started"] = "speaking_started"
    trans_id: int
    start_sample: int


class ResponsePayload_FinalTranscription(BaseModel):
    type: Literal["final_transcription"] = "final_transcription"
    trans_id: int
    transcription: str
    start_sample: int
    end_sample: int


class ResponsePayload_LipSyncViseme(BaseModel):
    type: Literal["lipsync_viseme"] = "lipsync_viseme"
    viseme: str
    probability: float
    start_sample: int
    end_sample: int


ResponsePayload = Annotated[
    ResponsePayload_Error
    | ResponsePayload_InterimTranscription
    | ResponsePayload_SpeakingStarted
    | ResponsePayload_FinalTranscription
    | ResponsePayload_LipSyncViseme,
    Field(discriminator="type"),
]


class Response(BaseModel):
    payload: ResponsePayload
    session_id: str


def engine_event_to_response_payload(
    evt: EngineEvent,
) -> ResponsePayload | Exception:
    if isinstance(evt, STTEvent_FinalTranscription):
        return ResponsePayload_FinalTranscription(
            trans_id=evt.trans_id,
            transcription=evt.transcription,
            start_sample=evt.start_sample,
            end_sample=evt.end_sample,
        )
    elif isinstance(evt, STTEvent_InterimTranscription):
        return ResponsePayload_InterimTranscription(
            trans_id=evt.trans_id,
            start_sample=evt.start_sample,
            end_sample=evt.end_sample,
            transcription=evt.transcription,
        )
    elif isinstance(evt, STTEvent_SpeakingStarted):
        return ResponsePayload_SpeakingStarted(
            trans_id=evt.trans_id,
            start_sample=evt.start_sample,
        )
    elif isinstance(evt, LipSyncEvent_Viseme):
        return ResponsePayload_LipSyncViseme(
            viseme=evt.viseme.name,
            probability=evt.probability,
            start_sample=evt.start_sample,
            end_sample=evt.end_sample,
        )

    raise Exception("Unknown event type")
