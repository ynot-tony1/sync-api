from typing_extensions import TypedDict
from typing import Union, Dict, List

JSONType = Union[str, int, float, bool, None, Dict[str, 'JSONType'], List['JSONType']]

LogConfig = Dict[str, JSONType]


class VideoProps(TypedDict):
    width: int
    height: int
    codec_name: str
    avg_frame_rate: str
    fps: float

class AudioProps(TypedDict, total=False):
    sample_rate: str
    channels: int
    codec_name: str


class SyncError(TypedDict):
    error: bool
    message: str
    final_offset: int


class ProcessSuccess(TypedDict):
    status: str  # e.g. "success"
    final_output: str
    message: str

class ProcessError(TypedDict, total=False):
    error: bool
    no_audio: bool
    no_video: bool
    no_fps: bool
    message: str
