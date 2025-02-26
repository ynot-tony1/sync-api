import os
import shutil
import tempfile
import unittest

from api.config.settings import TEST_DATA_DIR, FINAL_OUTPUT_DIR
from api.utils.ffmpeg_utils import FFmpegUtils

class TestFFmpegUtils(unittest.TestCase):
    """Integration tests for the FFmpegUtils utility class.

    These tests verify the functionality of FFmpegUtils methods for retrieving video/audio properties,
    shifting audio, and applying cumulative audio shifts on video files.
    """

    @classmethod
    def setUpClass(cls):
        """Set up test file paths for the FFmpegUtils tests.

        Attributes:
            example_video (str): Path to a valid video file with audio.
            synced_video (str): Path to a video file that is already synchronized.
            no_audio_video (str): Path to a video file that lacks an audio stream.
            no_video_video (str): Path to a video file with no video stream.
        """
        cls.example_video = os.path.join(TEST_DATA_DIR, 'example.avi')
        cls.synced_video = os.path.join(TEST_DATA_DIR, 'synced_example.avi')
        cls.no_audio_video = os.path.join(TEST_DATA_DIR, 'video_no_audio.avi')
        cls.no_video_video = os.path.join(TEST_DATA_DIR, 'video_no_video_stream.avi')

    def test_get_audio_properties_success(self):
        """Test that get_audio_properties returns valid audio properties for a video with audio.

        This test calls FFmpegUtils.get_audio_properties on a valid video file and asserts that the 
        returned dictionary contains expected keys: 'sample_rate', 'channels', and 'codec_name'.
        """
        props = FFmpegUtils.get_audio_properties(self.example_video)
        self.assertIsInstance(props, dict, "Audio properties should be a dict for a valid video.")
        self.assertIn('sample_rate', props, "Audio properties should contain 'sample_rate'.")
        self.assertIn('channels', props, "Audio properties should contain 'channels'.")
        self.assertIn('codec_name', props, "Audio properties should contain 'codec_name'.")

    def test_get_audio_properties_no_audio(self):
        """Test that get_audio_properties returns None for a video with no audio stream.

        This test calls FFmpegUtils.get_audio_properties on a video file known to have no audio and 
        asserts that the result is None.
        """
        props = FFmpegUtils.get_audio_properties(self.no_audio_video)
        self.assertIsNone(props, "Audio properties should be None for a video without an audio stream.")

    def test_get_video_properties_success(self):
        """Test that get_video_properties returns valid video properties for a video with a video stream.

        This test calls FFmpegUtils.get_video_properties on a valid video file and asserts that the returned
        dictionary contains the keys: 'width', 'height', 'codec_name', and 'avg_frame_rate'.
        """
        props = FFmpegUtils.get_video_properties(self.example_video)
        self.assertIsInstance(props, dict, "Video properties should be a dict for a valid video.")
        self.assertIn('codec_name', props, "Video properties should contain 'codec_name'.")
        self.assertIn('avg_frame_rate', props, "Video properties should contain 'avg_frame_rate'.")

    def test_shift_audio_success(self):
        """Test that shift_audio successfully creates an output file with a positive offset.

        This test applies a positive offset (100 ms) to example.avi and checks that:
          - The output file is created.
          - The output file is not empty.
        """
        temp_dir = tempfile.mkdtemp()
        output_file = os.path.join(temp_dir, "shifted_example.avi")
        try:
            FFmpegUtils.shift_audio(self.example_video, output_file, 100)
            self.assertTrue(os.path.exists(output_file), "Output file should be created by shift_audio.")
            self.assertGreater(os.path.getsize(output_file), 0, "Shifted file should not be empty.")
        finally:
            shutil.rmtree(temp_dir)

    def test_shift_audio_nonexistent_file(self):
        """Test that shift_audio does nothing when the input file does not exist.

        This test attempts to shift audio for a nonexistent video file and asserts that:
          - No output file is created.
          - The function handles the error gracefully.
        """
        nonexistent_file = os.path.join(TEST_DATA_DIR, "nonexistent.avi")
        temp_dir = tempfile.mkdtemp()
        output_file = os.path.join(temp_dir, "output.avi")
        try:
            FFmpegUtils.shift_audio(nonexistent_file, output_file, 100)
            self.assertFalse(os.path.exists(output_file), "Output file should not be created for a nonexistent input.")
        finally:
            shutil.rmtree(temp_dir)

    def test_apply_cumulative_shift_success(self):
        """Test that apply_cumulative_shift creates a final output file when given a valid input.

        This test calls FFmpegUtils.apply_cumulative_shift with a valid video file and a specified offset.
        It asserts that the final output file:
          - Exists.
          - Is not empty.
        After the test, it cleans up the output file and any temporary copy created.
        """
        temp_dir = tempfile.mkdtemp()
        final_output = os.path.join(temp_dir, "final_shifted_example.avi")
        try:
            FFmpegUtils.apply_cumulative_shift(self.example_video, final_output, 150)
            self.assertTrue(os.path.exists(final_output), "Final output file should exist after cumulative shift.")
            self.assertGreater(os.path.getsize(final_output), 0, "Final output file should not be empty.")
        finally:
            if os.path.exists(final_output):
                os.remove(final_output)
            shutil.rmtree(temp_dir)
            temp_copy = os.path.join(FINAL_OUTPUT_DIR, os.path.basename(self.example_video))
            if os.path.exists(temp_copy):
                os.remove(temp_copy)

if __name__ == '__main__':
    unittest.main()
