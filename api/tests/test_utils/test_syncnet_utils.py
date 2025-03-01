"""Tests for the SyncNetUtils asynchronous functions.

This module tests various asynchronous functions implemented in the SyncNetUtils class,
including running SyncNet, running the pipeline, preparing video, performing synchronization
iterations, finalizing synchronization, and the overall synchronization process. The tests
use the asyncio event loop to run asynchronous functions and patch external dependencies
to simulate expected behaviors.
"""

import os
import asyncio
import tempfile
import unittest
from unittest.mock import patch, MagicMock

from api.config.settings import FINAL_OUTPUT_DIR, LOGS_DIR, FINAL_LOGS_DIR, DATA_DIR
from api.utils.syncnet_utils import SyncNetUtils

# Dummy constants for testing
DUMMY_REF = "00001"
DUMMY_VIDEO_FILE = "/path/to/example.avi"
DUMMY_ORIGINAL_FILENAME = "example.avi"
# Expected destination is computed using DATA_DIR and the reference number "1"
EXPECTED_DESTINATION = os.path.join(DATA_DIR, f"1_{DUMMY_ORIGINAL_FILENAME}")
DUMMY_DESTINATION = EXPECTED_DESTINATION  
DUMMY_AVI_FILE = DUMMY_DESTINATION  
DUMMY_LOG_FILE = "/path/to/log/file.log"
DUMMY_VID_PROPS = {
    "codec_name": "mpeg4",
    "fps": 25.0,
    "avg_frame_rate": "25/1",
    "width": 640,
    "height": 480,
}
DUMMY_AUDIO_PROPS = {
    "sample_rate": "44100",
    "channels": 2,
    "codec_name": "pcm_s16le",
}

# Helper to wrap a value in an awaitable coroutine.
def async_return(result):
    """Wraps a value in a coroutine that returns that value.

    Args:
        result: The result to be returned by the coroutine.

    Returns:
        Coroutine that returns the given result.
    """
    async def _coro():
        return result
    return _coro()

# FakeProcess for simulating subprocess calls.
class FakeProcess:
    """A fake process to simulate asynchronous subprocess behavior.

    Attributes:
        stdout_bytes (bytes): The simulated output bytes.
        returncode (int): The simulated process return code.
    """
    def __init__(self, stdout_bytes, returncode=0):
        self.stdout_bytes = stdout_bytes
        self.returncode = returncode

    async def communicate(self):
        """Simulate process communication.

        Returns:
            tuple: A tuple containing stdout bytes and None for stderr.
        """
        return (self.stdout_bytes, None)

class TestSyncNetUtils(unittest.TestCase):
    """Tests for individual functions in the SyncNetUtils class."""

    def setUp(self):
        """Set up the asyncio event loop for test execution."""
        self.loop = asyncio.get_event_loop()

    @patch("api.utils.syncnet_utils.asyncio.create_subprocess_shell")
    def test_run_syncnet_success(self, mock_create_proc):
        """Test that run_syncnet returns the correct log file path on success.

        Mocks asyncio.create_subprocess_shell to return a FakeProcess with simulated log output.
        Asserts that the returned log file path matches the expected value.

        Args:
            mock_create_proc (MagicMock): The patched create_subprocess_shell.
        """
        ref_str = DUMMY_REF
        fake_log_file = os.path.join(FINAL_LOGS_DIR, f"run_{ref_str}.log")
        # Return a new FakeProcess wrapped in a coroutine.
        mock_create_proc.side_effect = lambda *args, **kwargs: async_return(FakeProcess(b"Fake log content", 0))
        
        returned_log = self.loop.run_until_complete(
            SyncNetUtils.run_syncnet(ref_str)
        )
        self.assertEqual(returned_log, fake_log_file)
        self.assertEqual(mock_create_proc.call_count, 1)

    @patch("api.utils.syncnet_utils.asyncio.create_subprocess_shell")
    def test_run_pipeline_success(self, mock_create_proc):
        """Test that run_pipeline executes without error.

        Mocks asyncio.create_subprocess_shell to return a FakeProcess with simulated output.
        Asserts that the pipeline runs successfully.

        Args:
            mock_create_proc (MagicMock): The patched create_subprocess_shell.
        """
        video_file = DUMMY_VIDEO_FILE
        ref = DUMMY_REF
        # Return a FakeProcess wrapped in a coroutine.
        mock_create_proc.side_effect = lambda *args, **kwargs: async_return(FakeProcess(b"Pipeline log content", 0))
        self.loop.run_until_complete(
            SyncNetUtils.run_pipeline(video_file, ref)
        )
        self.assertEqual(mock_create_proc.call_count, 1)

    @patch("api.utils.syncnet_utils.FFmpegUtils.reencode_to_avi", side_effect=lambda *args, **kwargs: async_return(None))
    @patch("api.utils.syncnet_utils.FileUtils.move_file", side_effect=lambda *args, **kwargs: DUMMY_DESTINATION)
    @patch("api.utils.syncnet_utils.FileUtils.copy_file", side_effect=lambda *args, **kwargs: "/tmp/dummy_temp.avi")
    @patch("api.utils.syncnet_utils.FFmpegUtils.get_video_properties", side_effect=lambda *args, **kwargs: async_return(DUMMY_VID_PROPS))
    @patch("api.utils.syncnet_utils.FFmpegUtils.get_audio_properties", side_effect=lambda *args, **kwargs: async_return(DUMMY_AUDIO_PROPS))
    @patch("os.path.exists", return_value=True)
    @patch("api.utils.syncnet_utils.FileUtils.get_next_directory_number", side_effect=lambda *args, **kwargs: "00001")
    def test_prepare_video_success(self, mock_get_next, mock_exists, mock_get_audio,
                                   mock_get_video, mock_copy, mock_move, mock_reencode):
        """Test that prepare_video successfully prepares a video without re-encoding.

        Mocks file operations and FFmpegUtils methods to simulate a scenario where the input file is
        already in AVI format. Asserts that the returned tuple matches expected dummy values.

        Args:
            mock_get_next (MagicMock): Patched get_next_directory_number.
            mock_exists (MagicMock): Patched os.path.exists.
            mock_get_audio (MagicMock): Patched FFmpegUtils.get_audio_properties.
            mock_get_video (MagicMock): Patched FFmpegUtils.get_video_properties.
            mock_copy (MagicMock): Patched FileUtils.copy_file.
            mock_move (MagicMock): Patched FileUtils.move_file.
            mock_reencode (MagicMock): Patched FFmpegUtils.reencode_to_avi.
        """
        result = self.loop.run_until_complete(
            SyncNetUtils.prepare_video(DUMMY_VIDEO_FILE, DUMMY_ORIGINAL_FILENAME)
        )
        (avi_file, vid_props, audio_props, fps, destination_path, reference_number) = result
        self.assertEqual(avi_file, DUMMY_DESTINATION)
        self.assertEqual(vid_props, DUMMY_VID_PROPS)
        self.assertEqual(audio_props, DUMMY_AUDIO_PROPS)
        self.assertEqual(fps, DUMMY_VID_PROPS.get("fps"))
        self.assertEqual(destination_path, DUMMY_DESTINATION)
        self.assertEqual(reference_number, int("00001"))
        mock_reencode.assert_not_called()

    @patch("api.utils.syncnet_utils.FFmpegUtils.shift_audio", side_effect=lambda *args, **kwargs: async_return(None))
    @patch("os.path.exists", return_value=True)
    @patch("api.utils.syncnet_utils.SyncNetUtils.run_syncnet", side_effect=lambda *args, **kwargs: async_return(DUMMY_LOG_FILE))
    @patch("api.utils.syncnet_utils.SyncNetUtils.run_pipeline", side_effect=lambda *args, **kwargs: async_return(None))
    @patch("api.utils.syncnet_utils.AnalysisUtils.analyze_syncnet_log")
    def test_perform_sync_iterations_success(self, mock_analyze, mock_run_pipeline,
                                               mock_run_syncnet, mock_exists, mock_shift_audio):
        """Test that perform_sync_iterations returns the correct cumulative shift and updated reference.

        Mocks analyze_syncnet_log to simulate a nonzero offset on the first iteration and zero on the second.
        Asserts that the returned total shift, corrected file, updated reference number, and iteration count are as expected.

        Args:
            mock_analyze (MagicMock): Patched AnalysisUtils.analyze_syncnet_log.
            mock_run_pipeline (MagicMock): Patched SyncNetUtils.run_pipeline.
            mock_run_syncnet (MagicMock): Patched SyncNetUtils.run_syncnet.
            mock_exists (MagicMock): Patched os.path.exists.
            mock_shift_audio (MagicMock): Patched FFmpegUtils.shift_audio.
        """
        # Simulate analyze_syncnet_log returning 10 on first call then 0 on second.
        mock_analyze.side_effect = [10, 0]
        result = self.loop.run_until_complete(
            SyncNetUtils.perform_sync_iterations(
                corrected_file=DUMMY_AVI_FILE,
                original_filename=DUMMY_ORIGINAL_FILENAME,
                fps=25.0,
                reference_number=1
            )
        )
        total_shift, final_file, updated_ref, iteration_count = result
        self.assertEqual(total_shift, 10)
        self.assertEqual(updated_ref, 2)
        self.assertIsInstance(final_file, str)
        self.assertTrue(final_file.endswith(".avi"))
        # Expected iteration_count is now 2 since two iterations were performed.
        self.assertEqual(iteration_count, 2)
        self.assertEqual(mock_analyze.call_count, 2)

    @patch("api.utils.syncnet_utils.os.remove")
    @patch("api.utils.syncnet_utils.FFmpegUtils.reencode_to_original_format", side_effect=lambda *args, **kwargs: async_return(None))
    @patch("api.utils.syncnet_utils.FFmpegUtils.apply_cumulative_shift", side_effect=lambda *args, **kwargs: async_return(None))
    @patch("os.path.exists", return_value=True)
    @patch("api.utils.syncnet_utils.AnalysisUtils.analyze_syncnet_log", return_value=0)
    @patch("api.utils.syncnet_utils.SyncNetUtils.run_pipeline", side_effect=lambda *args, **kwargs: async_return(None))
    @patch("api.utils.syncnet_utils.SyncNetUtils.run_syncnet", side_effect=lambda *args, **kwargs: async_return(DUMMY_LOG_FILE))
    def test_finalize_sync_success(self, mock_run_syncnet, mock_run_pipeline, mock_analyze,
                                   mock_exists, mock_apply_shift, mock_reencode, mock_remove):
        """Test that finalize_sync returns the correct final output path when the final offset is zero.

        Mocks FFmpegUtils.apply_cumulative_shift and other dependencies to simulate a successful finalization.
        Asserts that the returned final output path matches the expected value and that no re-encoding occurs.

        Args:
            mock_run_syncnet (MagicMock): Patched SyncNetUtils.run_syncnet.
            mock_run_pipeline (MagicMock): Patched SyncNetUtils.run_pipeline.
            mock_analyze (MagicMock): Patched AnalysisUtils.analyze_syncnet_log.
            mock_exists (MagicMock): Patched os.path.exists.
            mock_apply_shift (MagicMock): Patched FFmpegUtils.apply_cumulative_shift.
            mock_reencode (MagicMock): Patched FFmpegUtils.reencode_to_original_format.
            mock_remove (MagicMock): Patched os.remove.
        """
        final_out = self.loop.run_until_complete(
            SyncNetUtils.finalize_sync(
                input_file=DUMMY_VIDEO_FILE,
                original_filename=DUMMY_ORIGINAL_FILENAME,
                total_shift_ms=10,
                reference_number=1,
                fps=25.0,
                destination_path=DUMMY_DESTINATION,
                vid_props=DUMMY_VID_PROPS,
                audio_props=DUMMY_AUDIO_PROPS,
                corrected_file="/dummy/corrected.avi"
            )
        )
        expected_final = os.path.join(FINAL_OUTPUT_DIR, f"corrected_{DUMMY_ORIGINAL_FILENAME}")
        self.assertEqual(final_out, expected_final)
        mock_apply_shift.assert_called()
        mock_reencode.assert_not_called()

    @patch("api.utils.syncnet_utils.SyncNetUtils.finalize_sync", side_effect=lambda *args, **kwargs: async_return("/dummy/final_output.avi"))
    @patch("api.utils.syncnet_utils.SyncNetUtils.perform_sync_iterations", side_effect=lambda *args, **kwargs: async_return((10, "/dummy/final_corrected.avi", 2, 1)))
    def test_synchronize_video_success(self, mock_iterations, mock_finalize):
        """Test that synchronize_video returns the correct final output and sync status.

        Mocks perform_sync_iterations and finalize_sync to simulate a complete synchronization workflow.
        Asserts that the returned tuple matches the expected final output path and a flag indicating the clip is not already in sync.

        Args:
            mock_iterations (MagicMock): Patched SyncNetUtils.perform_sync_iterations.
            mock_finalize (MagicMock): Patched SyncNetUtils.finalize_sync.
        """
        result = self.loop.run_until_complete(
            SyncNetUtils.synchronize_video(
                avi_file=DUMMY_AVI_FILE,
                input_file=DUMMY_VIDEO_FILE,
                original_filename=DUMMY_ORIGINAL_FILENAME,
                vid_props=DUMMY_VID_PROPS,
                audio_props=DUMMY_AUDIO_PROPS,
                fps=25.0,
                destination_path=DUMMY_DESTINATION,
                reference_number=1
            )
        )
        self.assertEqual(result, ("/dummy/final_output.avi", False))
        mock_iterations.assert_called_once()
        mock_finalize.assert_called_once()


if __name__ == '__main__':
    unittest.main()
