#!/bin/bash

download_file "http://www.robots.ox.ac.uk/~vgg/software/lipsync/data/syncnet_v2.model" "syncnet_python/data/syncnet_v2.model"
download_file "http://www.robots.ox.ac.uk/~vgg/software/lipsync/data/example.avi" "syncnet_python/data/example.avi"

# Download pre-processing pipeline weights
download_file "https://www.robots.ox.ac.uk/~vgg/software/lipsync/data/sfd_face.pth" "syncnet_python/detectors/s3fd/weights/sfd_face.pth"

# Recreate gitignored directories
mkdir -p api/logs/final_logs
mkdir -p api/logs/run_logs
mkdir -p api/logs/logs
mkdir -p syncnet_python/file_handling/temp_input
mkdir -p syncnet_python/file_handling/final_output
