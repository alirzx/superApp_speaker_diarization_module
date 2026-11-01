from pydantic import BaseModel,Field
class Segment(BaseModel):
    start:float=Field(ge=0)
    end:float=Field(ge=0)
    speaker_id:str
class Result(BaseModel):
    request_id:str
    status:str='completed'
    model:str
    runtime:str
    audio_duration_seconds:float
    num_speakers:int
    speakers:list[str]
    segments:list[Segment]
    processing_time_ms:float
