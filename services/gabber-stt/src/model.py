from pydantic import BaseModel


class WordInfo(BaseModel):
    word: str
    start: float  # Start time in seconds
    end: float  # End time in seconds


class FullTranscript(BaseModel):
    transcript: str
    start_sample_index: int
    end_sample_index: int
    words: list["WordInfo"]
