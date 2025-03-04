from pydantic import BaseModel
from typing import Union, Dict

JSONType = Union[str, int, float, bool, None, dict, list]


class LogConfig(BaseModel):
    __root__: Dict[str, JSONType]

LogConfig.update_forward_refs()

class VideoProps(BaseModel):
    codec_name: str
    avg_frame_rate: str
    fps: float

class AudioProps(BaseModel):
    sample_rate: Union[str, None] = None
    channels: Union[int, None] = None
    codec_name: Union[str, None] = None

class SyncError(BaseModel):
    error: bool
    message: str
    final_offset: int

class ProcessSuccess(BaseModel):
    status: str
    final_output: str
    message: str

class ProcessError(BaseModel):
    error: bool
    no_audio: Union[bool, None] = None
    no_video: Union[bool, None] = None
    no_fps: Union[bool, None] = None
    message: str

class SyncAnalysisResult(BaseModel):
    best_offset_ms: int
    total_confidence: float
    confidence_mapping: Dict[int, float]
