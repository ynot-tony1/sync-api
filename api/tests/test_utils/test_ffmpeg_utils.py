import os
import shutil
import tempfile
import unittest

from api.config.type_settings import TEST_DATA_DIR, FINAL_OUTPUT_DIR
from api.utils.ffmpeg_utils import FFmpegUtils

class TestFFmpegUtils(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.example_video = os.path.join(TEST_DATA_DIR, 'example.avi')
        cls.synced_video = os.path.join(TEST_DATA_DIR, 'synced_example.avi')
        cls.no_audio_video = os.path.join(TEST_DATA_DIR, 'video_no_audio.avi')
        cls.no_video_video = os.path.join(TEST_DATA_DIR, 'video_no_video_stream.avi')




    def test_get_audio_properties_success(self):
        """Test that get_audio_properties returns valid audio info for a video with audio."""
        props = FFmpegUtils.get_audio_properties(self.example_video)
        self.assertIsInstance(props, dict, "Audio properties should be a dict for a valid video.")
        self.assertIn('sample_rate', props, "Audio properties should contain 'sample_rate'.")
        self.assertIn('channels', props, "Audio properties should contain 'channels'.")
        self.assertIn('codec_name', props, "Audio properties should contain 'codec_name'.")

    def test_get_audio_properties_no_audio(self):
        """Test that get_audio_properties returns None for a video with no audio stream."""
        props = FFmpegUtils.get_audio_properties(self.no_audio_video)
        self.assertIsNone(props, "Audio properties should be None for a video without an audio stream.")

    def test_get_video_properties_success(self):
        """Test that get_video_properties returns valid video info for a video with a video stream."""
        props = FFmpegUtils.get_video_properties(self.example_video)
        self.assertIsInstance(props, dict, "Video properties should be a dict for a valid video.")
        self.assertIn('width', props, "Video properties should contain 'width'.")
        self.assertIn('height', props, "Video properties should contain 'height'.")
        self.assertIn('codec_name', props, "Video properties should contain 'codec_name'.")
        self.assertIn('avg_frame_rate', props, "Video properties should contain 'avg_frame_rate'.")

    def test_shift_audio_success(self):
        """
        Test that shift_audio successfully creates an output file.
        This test applies a positive offset to example.avi.
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
        """
        Test that shift_audio does nothing (and logs an error) when the input file does not exist.
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
        """
        Test that apply_cumulative_shift creates a final output file when given a valid input.
        This function internally makes a temporary copy in FINAL_OUTPUT_DIR and then applies the shift.
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
