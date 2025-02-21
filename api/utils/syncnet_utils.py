import os
import subprocess
import logging
from .log_utils import LogUtils
from api.config.settings import LOGS_DIR, RUN_LOGS_DIR, DATA_WORK_DIR

LogUtils.configure_logging()
logger = logging.getLogger('pipeline_logger')

class SyncNetUtils:
    """Utility class for handling SyncNet operations."""

    @staticmethod
    def run_syncnet(ref_str, log_file=None):
        """
        Executes the SyncNet model and logs the output.

        Args:
            ref_str (str): Reference string identifier.
            log_file (str, optional): Custom path to the log file.
                                       If not provided, a default path based on ref_str is used.

        Returns:
            str: Path to the SyncNet log file.

        Raises:
            RuntimeError: If SyncNet execution fails.
        """
        # if log_file path is not provided, create it using the ref_str
        if log_file is None:
            log_file = os.path.join(RUN_LOGS_DIR, f"run_{ref_str}.log")
        
        # building the run syncnet command using module invocation (-m)
        cmd = [
            "python",
            "-m",            
            "syncnet_python.run_syncnet",
            "--data_dir", DATA_WORK_DIR,
            "--reference", ref_str
        ]

        try:
            # opening the log file in write mode to capture SyncNet's output
            with open(log_file, 'w') as log:
                # running the SyncNet command, redirecting both stdout and stderr to the log file
                subprocess.run(cmd, stdout=log, stderr=subprocess.STDOUT, check=True)
            logger.info(f"SyncNet model completed successfully. Log saved to: {log_file}")
        
        except subprocess.CalledProcessError as e:
            error_msg = f"SyncNet failed while processing reference {ref_str}: {e}"
            logger.error(error_msg)
            raise RuntimeError(error_msg) from e

        return log_file


    @staticmethod
    def run_pipeline(video_file, ref):
        """
        Runs the SyncNet pipeline on a given video file.

        Args:
            video_file (str): Path to the video file.
            ref (str): Reference string identifier.

        Raises:
            RuntimeError: If the pipeline execution fails.
        """
        # building the command to run the syncnet pipeline using module invocation (-m)
        cmd = [
            "python",
            "-m",
            "syncnet_python.run_pipeline",
            "--videofile", video_file,
            "--reference", ref
        ]
        log_file = os.path.join(LOGS_DIR, 'pipeline.log')
        try:
            # opening the pipeline.log file in write mode to store the pipeline's output
            with open(log_file, 'w') as log:
                # running the syncnet pipeline command and redirecting stdout and stderr to the log file
                subprocess.run(cmd, stdout=log, stderr=subprocess.STDOUT, check=True)
            logger.info(f"SyncNet pipeline successfully executed for video: {video_file} with reference: {ref}")
        except subprocess.CalledProcessError as e:
            logger.error(f"SyncNet pipeline failed for video {video_file} (ref={ref}): {e}")
            # raising a runtime error with the error message in it
            raise RuntimeError(f"SyncNet pipeline failed for video {video_file} (ref={ref}): {e}") from e
