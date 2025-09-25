from pydantic import BaseModel, Field
from typing import Literal, Annotated


class RequestPayload(BaseModel):
    type: Literal["start", "stop"]


class ResponsePayload_Error(BaseModel):
    type: Literal["error"] = "error"
    message: str


class ResponsePayload_Transcription(BaseModel):
    type: Literal["transcription"] = "transcription"
    start_sample: int
    end_sample: int
    words: list
    transcription: str


class Response(BaseModel):
    payload: ResponsePayload_Error = Field(discriminator="type")
