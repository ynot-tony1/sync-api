"""Default video processor implementation.

This module provides the DefaultVideoProcessor class, which implements
the VideoProcessorInterface by delegating to the concrete `process_video`
function defined in `api.process_video`.
"""

from typing import Union
from api.interfaces.video_processor import VideoProcessorInterface
from api.types.props import ProcessSuccess, ProcessError
from api.process_video import process_video as concrete_process_video


class DefaultVideoProcessor(VideoProcessorInterface):
    """A default implementation of VideoProcessorInterface.

    Uses the `concrete_process_video` function to perform the actual
    video processing work.
    """

    async def process_video(
        self,
        input_file: str,
        original_filename: str
    ) -> Union[ProcessSuccess, ProcessError]:
        """Process a video file asynchronously.

        Delegates to the `concrete_process_video` function, returning
        either a success or an error result.

        Args:
            input_file (str): The path to the video file to be processed.
            original_filename (str): The original name of the file, used
                for logging or metadata purposes.

        Returns:
            Union[ProcessSuccess, ProcessError]:
                - ProcessSuccess: Contains details about the successful
                  processing (e.g., output file path, processing time).
                - ProcessError: Contains error information if processing failed.
        """
        return await concrete_process_video(input_file, original_filename)
