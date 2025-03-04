"""
Tests for the SyncNetUtils asynchronous functions.

This module contains unit tests for the SyncNetUtils class, which handles asynchronous
video synchronization tasks. The tests use asyncio and unittest.mock to simulate
asynchronous behavior and external dependencies.

The tests cover the following functionality:
- Running the SyncNet process.
- Preparing a video for synchronization.
- Performing iterative synchronization.
- Finalizing the synchronization process.
"""

import os
import asyncio
import unittest
from unittest.mock import patch, MagicMock

from api.config.settings import DATA_DIR
from api.utils.syncnet_utils import SyncNetUtils
from api.types.props import SyncAnalysisResult

# Dummy constants for testing
DUMMY_REF = "00001"
DUMMY_VIDEO_FILE = "/path/to/example.avi"
DUMMY_ORIGINAL_FILENAME = "example.avi"
DUMMY_DESTINATION = os.path.join(DATA_DIR, "1_example.avi")
DUMMY_VID_PROPS = {"codec_name": "mpeg4", "fps": 25.0}
DUMMY_AUDIO_PROPS = {"sample_rate": "44100", "channels": 2}


class TestSyncNetUtils(unittest.TestCase):
    """Test suite for the SyncNetUtils class.

    This class contains unit tests for the asynchronous methods in the SyncNetUtils class.
    Each test method is designed to validate a specific functionality of the class.
    """

    def setUp(self):
        """Set up the test environment.

        Initializes a new event loop for each test and sets it as the default loop.
        This ensures that all asynchronous operations run within the same event loop.
        """
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

    def async_test(f):
        """Decorator to run async test methods in the event loop.

        Args:
            f (Callable): The asynchronous test function to wrap.

        Returns:
            Callable: A wrapper function that runs the test in the event loop.
        """
        def wrapper(*args, **kwargs):
            return args[0].loop.run_until_complete(f(*args, **kwargs))
        return wrapper

    @patch("api.utils.syncnet_utils.asyncio.create_subprocess_shell")
    @async_test
    async def test_run_syncnet_success(self, mock_subprocess):
        """Tests successful execution of the run_syncnet method.

        This test verifies that the run_syncnet method correctly executes the SyncNet process
        and returns the path to the log file.

        Args:
            mock_subprocess (MagicMock): Mock for asyncio.create_subprocess_shell.
        """
        process_mock = MagicMock()
        communicate_future = asyncio.Future()
        communicate_future.set_result((b"dummy output", None))
        process_mock.communicate.return_value = communicate_future
        process_mock.returncode = 0

        async def create_subprocess_coro(*args, **kwargs):
            return process_mock

        mock_subprocess.side_effect = create_subprocess_coro

        result = await SyncNetUtils.run_syncnet(DUMMY_REF)
        self.assertIn("run_00001.log", result, "The returned log file name should contain 'run_00001.log'.")
        mock_subprocess.assert_called_once()
        process_mock.communicate.assert_called_once()

    @patch("api.utils.syncnet_utils.os.path.exists")
    @patch("api.utils.syncnet_utils.FileUtils.move_file")
    @patch("api.utils.syncnet_utils.FileUtils.copy_file")
    @patch("api.utils.syncnet_utils.FileUtils.get_next_directory_number")
    @patch("api.utils.syncnet_utils.DATA_DIR", "/mocked/data/dir")
    @async_test
    async def test_prepare_video_success(self, mock_get_next_dir, mock_copy, mock_move, mock_exists):
        """Tests successful execution of prepare_video with mocked file operations.

        This test verifies that prepare_video correctly prepares a video for synchronization
        by copying, moving, retrieving video/audio properties, and (if needed) re-encoding.

        Args:
            mock_get_next_dir (MagicMock): Mock for FileUtils.get_next_directory_number.
            mock_copy (MagicMock): Mock for FileUtils.copy_file.
            mock_move (MagicMock): Mock for FileUtils.move_file.
            mock_exists (MagicMock): Mock for os.path.exists.
        """
        mock_get_next_dir.return_value = asyncio.Future()
        mock_get_next_dir.return_value.set_result("1")
        mocked_destination = "/mocked/data/dir/1_example.avi"
        mock_exists.return_value = True
        mock_copy.return_value = asyncio.Future()
        mock_copy.return_value.set_result("/temp/path")
        mock_move.return_value = asyncio.Future()
        mock_move.return_value.set_result(mocked_destination)
        vid_future = asyncio.Future()
        vid_future.set_result(DUMMY_VID_PROPS)
        aud_future = asyncio.Future()
        aud_future.set_result(DUMMY_AUDIO_PROPS)

        with patch("api.utils.syncnet_utils.FFmpegUtils.get_video_properties") as mock_vid, \
             patch("api.utils.syncnet_utils.FFmpegUtils.get_audio_properties") as mock_aud:
            mock_vid.return_value = vid_future
            mock_aud.return_value = aud_future
            result = await SyncNetUtils.prepare_video(DUMMY_VIDEO_FILE, DUMMY_ORIGINAL_FILENAME)
            self.assertEqual(result[0], mocked_destination,
                             "The AVI file path should match the mocked destination.")

    @patch("api.utils.syncnet_utils.os.path.exists")
    @async_test
    async def test_perform_sync_iterations(self, mock_exists):
        """Tests perform_sync_iterations for iterative synchronization.

        This test verifies that perform_sync_iterations correctly iterates until the computed
        offset is zero, aggregating the total shift and updating the corrected file path.

        Args:
            mock_exists (MagicMock): Mock for os.path.exists.
        """
        mock_exists.return_value = True

        # Update the futures to return proper SyncAnalysisResult objects.
        future1 = asyncio.Future()
        future1.set_result(SyncAnalysisResult(best_offset_ms=100, total_confidence=100.0, confidence_mapping={}))
        future2 = asyncio.Future()
        future2.set_result(SyncAnalysisResult(best_offset_ms=0, total_confidence=0.0, confidence_mapping={}))

        with patch("api.utils.syncnet_utils.AnalysisUtils.analyze_syncnet_log") as mock_analyze, \
             patch("api.utils.syncnet_utils.SyncNetUtils.run_pipeline") as mock_pipeline, \
             patch("api.utils.syncnet_utils.SyncNetUtils.run_syncnet") as mock_syncnet, \
             patch("api.utils.syncnet_utils.FFmpegUtils.shift_audio") as mock_shift:
            mock_analyze.side_effect = [future1, future2]
            mock_pipeline.return_value = asyncio.Future()
            mock_pipeline.return_value.set_result(None)
            mock_syncnet.return_value = asyncio.Future()
            mock_syncnet.return_value.set_result("dummy.log")
            mock_shift.return_value = asyncio.Future()
            mock_shift.return_value.set_result(None)

            result = await SyncNetUtils.perform_sync_iterations(DUMMY_DESTINATION,
                                                                DUMMY_ORIGINAL_FILENAME,
                                                                25.0, 1)
            self.assertEqual(result[0], 100,
                             "The total shift in ms should be 100 after the first iteration.")

    @patch("api.utils.syncnet_utils.os.remove")
    @patch("api.utils.syncnet_utils.FFmpegUtils.apply_cumulative_shift")
    @async_test
    async def test_finalize_sync_success(self, mock_shift, mock_remove):
        """Tests finalize_sync for successful finalization.

        This test verifies that finalize_sync applies the cumulative audio shift, runs the final
        verification, and returns a final output path that includes 'corrected'.

        Args:
            mock_shift (MagicMock): Mock for FFmpegUtils.apply_cumulative_shift.
            mock_remove (MagicMock): Mock for os.remove.
        """
        # Update the analyze_future to return a proper SyncAnalysisResult.
        analyze_future = asyncio.Future()
        analyze_future.set_result(SyncAnalysisResult(best_offset_ms=0, total_confidence=0.0, confidence_mapping={}))

        with patch("api.utils.syncnet_utils.AnalysisUtils.analyze_syncnet_log") as mock_analyze, \
             patch("api.utils.syncnet_utils.SyncNetUtils.run_pipeline") as mock_pipeline, \
             patch("api.utils.syncnet_utils.SyncNetUtils.run_syncnet") as mock_syncnet:
            mock_analyze.return_value = analyze_future
            mock_pipeline.return_value = asyncio.Future()
            mock_pipeline.return_value.set_result(None)
            mock_syncnet.return_value = asyncio.Future()
            mock_syncnet.return_value.set_result("dummy.log")
            mock_shift.return_value = asyncio.Future()
            mock_shift.return_value.set_result(None)

            result = await SyncNetUtils.finalize_sync(DUMMY_VIDEO_FILE,
                                                       DUMMY_ORIGINAL_FILENAME,
                                                       100,
                                                       1,
                                                       25.0,
                                                       DUMMY_DESTINATION,
                                                       DUMMY_VID_PROPS,
                                                       DUMMY_AUDIO_PROPS,
                                                       DUMMY_DESTINATION)
            self.assertIn("corrected", result,
                          "The final output path should contain 'corrected' indicating a successful sync.")

if __name__ == "__main__":
    unittest.main()
