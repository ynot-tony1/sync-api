import unittest
import os
from utils.ffmpeg_utils import FFmpegUtils  # Ensure this import is correct
from settings import TEST_DATA_DIR


class TestFFmpegUtils(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """
        Setting up some class wide resources 
        """
        # path to the test_data directory
        cls.input_file = os.path.join(TEST_DATA_DIR , 'example.avi')
        # expected audio properties are based on the known outputs from a manual ffprobe of example.avi
        cls.expected_audio_props = {
            'sample_rate': '16000',        # expected sample rate
            'channels': 1,                 # example number of channels
            'codec_name': 'pcm_s16le'      # example codec
        }
    # testing get_audio_properties with a known output
    def test_get_audio_properties_success(self):
        """
        Testing that FFmpegUtils.get_audio_properties returns correct properties for a valid audio file.
        """
        
        # calling the method to get audio properties
        audio_props = FFmpegUtils.get_audio_properties(self.input_file)
        
        # checking sample rate
        self.assertEqual(
            audio_props['sample_rate'], 
            self.expected_audio_props['sample_rate'],
            f"Expected 'sample_rate' to be {self.expected_audio_props['sample_rate']}, got {audio_props['sample_rate']}."
        )
        
        # checking 'channels'
        self.assertEqual(
            audio_props['channels'], 
            self.expected_audio_props['channels'],
            f"Expected 'channels' to be {self.expected_audio_props['channels']}, got {audio_props['channels']}."
        )
        # checking codec
        self.assertEqual(
            audio_props['codec_name'], 
            self.expected_audio_props['codec_name'],
            f"Expected 'codec_name' to be {self.expected_audio_props['codec_name']}, got {audio_props['codec_name']}."
        )

if __name__ == '__main__':
    unittest.main()
