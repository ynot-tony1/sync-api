"""Video processor interface module.

This module defines the VideoProcessorInterface abstract base class,
which specifies the contract for any video processor implementation.
"""

from abc import ABC, abstractmethod
from typing import Union
from api.types.props import ProcessSuccess, ProcessError


class VideoProcessorInterface(ABC):
    """Abstract base class for video processing.

    Any concrete video processor must implement the `process_video` method
    to handle the processing of video files and return a standardized result.
    """

    @abstractmethod
    async def process_video(
        self,
        input_file: str,
        original_filename: str
    ) -> Union[ProcessSuccess, ProcessError]:
        """Process a video file asynchronously.

        Implementations should perform all necessary steps to process the given
        video, such as transcoding, filtering, or analysis, and return either
        a success or error result.

        Args:
            input_file (str): The file path to the video to be processed.
            original_filename (str): The original filename of the video, which
                may be used for logging, metadata, or output naming.

        Returns:
            Union[ProcessSuccess, ProcessError]:
                - ProcessSuccess: Contains information about the processed
                  video on success (e.g., output path, duration, metadata).
                - ProcessError: Contains error details if processing fails.
        """
        pass
