from pydantic import BaseModel, Field
from typing import Literal, Annotated


class RequestPayload_StartSession(BaseModel):
    type: Literal["start_session"] = "start_session"
    sample_rate: int


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


class ResponsePayload_Transcription(BaseModel):
    type: Literal["transcription"] = "transcription"
    start_sample: int
    end_sample: int
    words: list
    transcription: str


ResponsePayload = Annotated[
    ResponsePayload_Error | ResponsePayload_Transcription,
    Field(discriminator="type"),
]


class Response(BaseModel):
    payload: ResponsePayload
    session_id: str
