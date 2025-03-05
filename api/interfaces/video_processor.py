from abc import ABC, abstractmethod
from typing import Union
from api.types.props import ProcessSuccess, ProcessError

class VideoProcessorInterface(ABC):
    @abstractmethod
    async def process_video(
        self, 
        input_file: str, 
        original_filename: str
    ) -> Union[ProcessSuccess, ProcessError]:
        """
        Processes a video file and returns either a success or error response.
        """
        pass
