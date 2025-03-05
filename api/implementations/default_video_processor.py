# api/implementations/default_video_processor.py
from typing import Union
from api.interfaces.video_processor import VideoProcessorInterface
from api.types.props import ProcessSuccess, ProcessError
from api.process_video import process_video as concrete_process_video

class DefaultVideoProcessor(VideoProcessorInterface):
    async def process_video(
        self, 
        input_file: str, 
        original_filename: str
    ) -> Union[ProcessSuccess, ProcessError]:
        return await concrete_process_video(input_file, original_filename)
