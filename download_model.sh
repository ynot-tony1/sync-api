#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e

# Enable verbose output
set -x

echo "=== Starting download_model.sh ==="

# Function to download a file with verification
download_file() {
    local url=$1
    local output_path=$2

    echo "Downloading from $url to $output_path"

    # Create the directory if it doesn't exist
    mkdir -p "$(dirname "$output_path")"

    # Download the file with progress bar
    wget --progress=dot:giga "$url" -O "$output_path"

    # Verify the download
    if [[ -f "$output_path" ]]; then
        echo "Successfully downloaded $output_path"
    else
        echo "Failed to download $output_path"
        exit 1
    fi
}

# Download SyncNet model and example video
download_file "http://www.robots.ox.ac.uk/~vgg/software/lipsync/data/syncnet_v2.model" "syncnet_python/data/syncnet_v2.model"
download_file "http://www.robots.ox.ac.uk/~vgg/software/lipsync/data/example.avi" "syncnet_python/data/example.avi"

# Download pre-processing pipeline weights
download_file "https://www.robots.ox.ac.uk/~vgg/software/lipsync/data/sfd_face.pth" "syncnet_python/detectors/s3fd/weights/sfd_face.pth"

# Recreate gitignored directories
echo "Creating necessary directories..."
mkdir -p api/logs/final_logs
mkdir -p api/logs/run_logs
mkdir -p api/logs/logs
mkdir -p syncnet_python/file_handling/temp_input
mkdir -p syncnet_python/file_handling/final_output

echo "=== Completed download_model.sh ==="

# List the contents of the downloaded directories for verification
echo "=== Verifying Downloads ==="
echo "Contents of syncnet_python/data/:"
ls -la syncnet_python/data/

echo "Contents of syncnet_python/detectors/s3fd/weights/:"
ls -la syncnet_python/detectors/s3fd/weights/

echo "Contents of api/logs/logs/:"
ls -la api/logs/logs/

echo "Contents of syncnet_python/file_handling/temp_input/:"
ls -la syncnet_python/file_handling/temp_input/

echo "Contents of syncnet_python/file_handling/final_output/:"
ls -la syncnet_python/file_handling/final_output/

echo "=== download_model.sh finished successfully ==="
