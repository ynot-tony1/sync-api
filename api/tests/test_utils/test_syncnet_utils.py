import os
import unittest
from unittest.mock import patch, mock_open

from api.config.type_settings import (
    FINAL_OUTPUT_DIR, LOGS_DIR, FINAL_LOGS_DIR,
)
from api.utils.syncnet_utils import SyncNetUtils

DUMMY_REF = "00001"
DUMMY_VIDEO_FILE = "/path/to/example.avi"
DUMMY_ORIGINAL_FILENAME = "example.avi"
DUMMY_DESTINATION = "/path/to/destination/example.avi"
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


class TestSyncNetUtils(unittest.TestCase):
    """Test suite for the SyncNetUtils class methods.

    This test suite verifies the functionality of the SyncNetUtils class, which is responsible for
    synchronizing video and audio streams using various subprocess calls and FFmpeg operations.
    Each test simulates a specific part of the synchronization pipeline using mocks to avoid
    external dependencies such as file I/O and subprocess execution.

    Attributes:
        None
    """

    @patch("api.utils.syncnet_utils.subprocess.run")
    def test_run_syncnet_success(self, mock_run):
        """Test run_syncnet for successful execution and correct log file generation.

        This test verifies that the SyncNetUtils.run_syncnet function correctly constructs and returns
        the expected log file path when the underlying subprocess command executes successfully. The test
        mocks subprocess.run to simulate command execution and builtins.open to simulate file I/O operations.

        Mocks:
            subprocess.run: Simulated using `mock_run` to represent successful command execution.
            builtins.open: Patched with `mock_open` to avoid actual file operations.

        Args:
            mock_run (MagicMock): A mock object replacing subprocess.run to intercept command execution.

        Returns:
            None: The test asserts that the returned log file path matches the expected format based on the
            provided reference string.
        """
        ref_str = DUMMY_REF
        fake_log_file = os.path.join(FINAL_LOGS_DIR, f"run_{ref_str}.log")
        m = mock_open()
        with patch("builtins.open", m):
            returned_log = SyncNetUtils.run_syncnet(ref_str)
        self.assertEqual(returned_log, fake_log_file)
        mock_run.assert_called_once()

    @patch("api.utils.syncnet_utils.subprocess.run")
    def test_run_pipeline_success(self, mock_run):
        """Test run_pipeline for successful pipeline execution.

        This test ensures that the SyncNetUtils.run_pipeline function executes the pipeline process without
        raising any exceptions. It mocks subprocess.run to simulate a successful pipeline run and patches
        builtins.open to simulate log file creation.

        Mocks:
            subprocess.run: Replaced by `mock_run` to simulate the execution of the pipeline command.
            builtins.open: Patched with `mock_open` to simulate file I/O operations without disk access.

        Args:
            mock_run (MagicMock): A mock object substituting subprocess.run.

        Returns:
            None: The test verifies that the pipeline executes successfully and that subprocess.run is called once.
        """
        video_file = DUMMY_VIDEO_FILE
        ref = DUMMY_REF
        fake_log_file = os.path.join(LOGS_DIR, "pipeline.log")
        m = mock_open()
        with patch("builtins.open", m):
            SyncNetUtils.run_pipeline(video_file, ref)
        mock_run.assert_called_once()

    @patch("api.utils.syncnet_utils.FFmpegUtils.reencode_to_avi")
    @patch("api.utils.syncnet_utils.FileUtils.move_to_data_work")
    @patch("api.utils.syncnet_utils.FileUtils.copy_input_to_temp")
    @patch("api.utils.syncnet_utils.FFmpegUtils.get_video_properties")
    @patch("api.utils.syncnet_utils.FFmpegUtils.get_audio_properties")
    @patch("os.path.exists")
    @patch("api.utils.syncnet_utils.FileUtils.get_next_directory_number")
    def test_prepare_video_success(self, mock_get_next, mock_exists, mock_get_audio,
                                   mock_get_video, mock_copy, mock_move, mock_reencode):
        """Test prepare_video for successful video preparation without re-encoding.

        This test verifies that the SyncNetUtils.prepare_video function processes the input video file correctly,
        returning a tuple containing the AVI file path, video properties, audio properties, frame rate, destination
        path, and a reference number. Given that the original file extension is '.avi', the function should bypass
        the re-encoding step, and the returned AVI file should match the expected destination.

        Mocks:
            FileUtils.get_next_directory_number: Simulated to return a dummy reference number.
            FileUtils.copy_input_to_temp: Mocked to return a temporary file path.
            FileUtils.move_to_data_work: Simulated to return the expected destination path.
            os.path.exists: Patched to always return True, indicating file existence.
            FFmpegUtils.get_video_properties: Returns predefined dummy video properties.
            FFmpegUtils.get_audio_properties: Returns predefined dummy audio properties.
            FFmpegUtils.reencode_to_avi: Verified not to be called because the file is already in AVI format.

        Args:
            mock_get_next (MagicMock): Mock for obtaining the next directory number.
            mock_exists (MagicMock): Mock for checking file existence.
            mock_get_audio (MagicMock): Mock for retrieving audio properties.
            mock_get_video (MagicMock): Mock for retrieving video properties.
            mock_copy (MagicMock): Mock for copying the input file to a temporary location.
            mock_move (MagicMock): Mock for moving the file to the designated data directory.
            mock_reencode (MagicMock): Mock for re-encoding to AVI, which should not be invoked for AVI files.

        Returns:
            None: The test asserts that the function returns the correct tuple and that re-encoding is skipped.
        """
        mock_get_next.return_value = "00001"
        mock_copy.return_value = "/tmp/dummy_temp.avi"
        mock_move.return_value = DUMMY_DESTINATION
        mock_exists.return_value = True
        mock_get_video.return_value = DUMMY_VID_PROPS
        mock_get_audio.return_value = DUMMY_AUDIO_PROPS

        result = SyncNetUtils.prepare_video(DUMMY_VIDEO_FILE, DUMMY_ORIGINAL_FILENAME)
        (avi_file, vid_props, audio_props, fps, destination_path, reference_number) = result
        self.assertEqual(avi_file, DUMMY_DESTINATION)
        self.assertEqual(vid_props, DUMMY_VID_PROPS)
        self.assertEqual(audio_props, DUMMY_AUDIO_PROPS)
        self.assertEqual(fps, DUMMY_VID_PROPS.get("fps"))
        self.assertEqual(destination_path, DUMMY_DESTINATION)
        self.assertEqual(reference_number, int("00001"))
        mock_reencode.assert_not_called()

    @patch("api.utils.syncnet_utils.FFmpegUtils.shift_audio")
    @patch("os.path.exists")
    @patch("api.utils.syncnet_utils.SyncNetUtils.run_syncnet")
    @patch("api.utils.syncnet_utils.SyncNetUtils.run_pipeline")
    @patch("api.utils.syncnet_utils.AnalysisUtils.analyze_syncnet_log")
    def test_perform_sync_iterations_success(self, mock_analyze, mock_run_pipeline,
                                               mock_run_syncnet, mock_exists, mock_shift_audio):
        """Test perform_sync_iterations for correct cumulative shift calculation and reference update.

        This test verifies that the SyncNetUtils.perform_sync_iterations function correctly aggregates the audio
        shift over multiple iterations, updates the reference number, and returns a valid final corrected file path.
        By setting side effects on the analyze_syncnet_log mock, the test simulates successive offset values and
        ensures that the iteration terminates appropriately when no further shift is needed.

        Mocks:
            AnalysisUtils.analyze_syncnet_log: Simulated to return a sequence of offsets (e.g., 10 then 0).
            os.path.exists: Always returns True to simulate the existence of necessary files.
            SyncNetUtils.run_pipeline: Patched to simulate a successful pipeline run.
            SyncNetUtils.run_syncnet: Patched to simulate log generation for each iteration.
            FFmpegUtils.shift_audio: Patched to simulate audio shifting operations.

        Args:
            mock_analyze (MagicMock): Mock for analyzing the SyncNet log to obtain audio offset values.
            mock_run_pipeline (MagicMock): Mock for executing the pipeline.
            mock_run_syncnet (MagicMock): Mock for running the SyncNet process.
            mock_exists (MagicMock): Mock for file existence checks.
            mock_shift_audio (MagicMock): Mock for applying the audio shift corrections.

        Returns:
            None: The test asserts that the cumulative shift, updated reference number, and final corrected file path
            match the expected values.
        """
        mock_analyze.side_effect = [10, 0]
        mock_exists.return_value = True
        total_shift, final_file, updated_ref = SyncNetUtils.perform_sync_iterations(
            corrected_file=DUMMY_AVI_FILE,
            original_filename=DUMMY_ORIGINAL_FILENAME,
            fps=25.0,
            reference_number=1
        )
        self.assertEqual(total_shift, 10)
        self.assertEqual(updated_ref, 2)
        self.assertIsInstance(final_file, str)
        self.assertTrue(final_file.endswith(".avi"))
        self.assertEqual(mock_analyze.call_count, 2)

    @patch("api.utils.syncnet_utils.os.remove")
    @patch("api.utils.syncnet_utils.FFmpegUtils.reencode_to_original_format")
    @patch("api.utils.syncnet_utils.FFmpegUtils.apply_cumulative_shift")
    @patch("os.path.exists")
    @patch("api.utils.syncnet_utils.AnalysisUtils.analyze_syncnet_log")
    @patch("api.utils.syncnet_utils.SyncNetUtils.run_pipeline")
    @patch("api.utils.syncnet_utils.SyncNetUtils.run_syncnet", return_value=DUMMY_LOG_FILE)
    def test_finalize_sync_success(self, mock_run_syncnet, mock_run_pipeline, mock_analyze,
                                   mock_exists, mock_apply_shift, mock_reencode, mock_remove):
        """Test finalize_sync for finalizing synchronization with no additional audio offset.

        This test verifies that the SyncNetUtils.finalize_sync function produces the correct final output path
        when analysis of the SyncNet log indicates no further audio shift (i.e., returns 0). It confirms that the
        cumulative shift is applied and that re-encoding is skipped for AVI files.

        Mocks:
            AnalysisUtils.analyze_syncnet_log: Returns 0 to simulate no additional offset.
            os.path.exists: Always returns True, indicating file existence.
            SyncNetUtils.run_syncnet: Patched to return a dummy log file path.
            SyncNetUtils.run_pipeline: Patched to simulate pipeline execution.
            FFmpegUtils.apply_cumulative_shift: Verified to be called to apply audio shift corrections.
            FFmpegUtils.reencode_to_original_format: Should not be called since re-encoding is unnecessary.
            os.remove: Patched to simulate removal of temporary files.

        Args:
            mock_run_syncnet (MagicMock): Mock for running SyncNet, returning a dummy log file.
            mock_run_pipeline (MagicMock): Mock for executing the pipeline.
            mock_analyze (MagicMock): Mock for analyzing the SyncNet log.
            mock_exists (MagicMock): Mock for checking file existence.
            mock_apply_shift (MagicMock): Mock for applying the cumulative audio shift.
            mock_reencode (MagicMock): Mock for re-encoding to the original format.
            mock_remove (MagicMock): Mock for removing temporary files.

        Returns:
            None: The test asserts that the final output path matches the expected result and that re-encoding is not invoked.
        """
        mock_analyze.return_value = 0
        mock_exists.return_value = True
        final_out = SyncNetUtils.finalize_sync(
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
        expected_final = os.path.join(FINAL_OUTPUT_DIR, f"corrected_{DUMMY_ORIGINAL_FILENAME}")
        self.assertEqual(final_out, expected_final)
        mock_apply_shift.assert_called()
        mock_reencode.assert_not_called()

    @patch("api.utils.syncnet_utils.SyncNetUtils.finalize_sync")
    @patch("api.utils.syncnet_utils.SyncNetUtils.perform_sync_iterations")
    def test_synchronize_video_success(self, mock_iterations, mock_finalize):
        """Test synchronize_video for full video synchronization process.

        This test verifies that the SyncNetUtils.synchronize_video function correctly integrates the iterative
        synchronization phase and the finalization phase to produce the expected final output video. It mocks the
        perform_sync_iterations and finalize_sync methods to simulate the complete synchronization workflow.

        Mocks:
            SyncNetUtils.perform_sync_iterations: Simulated to return dummy cumulative shift, a final corrected file path,
                and an updated reference number.
            SyncNetUtils.finalize_sync: Simulated to return a dummy final output video path.

        Args:
            mock_iterations (MagicMock): Mock for performing iterative synchronization.
            mock_finalize (MagicMock): Mock for finalizing synchronization.

        Returns:
            None: The test asserts that the overall synchronization process returns the correct final output path.
        """
        mock_iterations.return_value = (10, "/dummy/final_corrected.avi", 2)
        mock_finalize.return_value = "/dummy/final_output.avi"
        result = SyncNetUtils.synchronize_video(
            avi_file=DUMMY_AVI_FILE,
            input_file=DUMMY_VIDEO_FILE,
            original_filename=DUMMY_ORIGINAL_FILENAME,
            vid_props=DUMMY_VID_PROPS,
            audio_props=DUMMY_AUDIO_PROPS,
            fps=25.0,
            destination_path=DUMMY_DESTINATION,
            reference_number=1
        )
        self.assertEqual(result, "/dummy/final_output.avi")
        mock_iterations.assert_called_once()
        mock_finalize.assert_called_once()


if __name__ == '__main__':
    unittest.main()
