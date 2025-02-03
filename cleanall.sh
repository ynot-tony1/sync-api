#!/bin/bash

# Deletes all contents of final_output
find ./api/file_handling/final_output -mindepth 1 -exec rm -rf {} +

# Deletes all .avi files in data/work
find ./syncnet_python/data -type f -name '*.avi' -exec rm -f {} +

# Deletes all pipeline processing directories matching numeric patterns
find ./syncnet_python/data/work -type d -regex '.*/[0-9]+' -exec rm -r {} +

# Deletes all final logs
find ./api/logs/final_logs -mindepth 1 -exec rm -rf {} +

# Deletes all run logs
find ./api/logs/run_logs -mindepth 1 -exec rm -rf {} +

# Deletes all processing logs
find ./api/logs/logs -mindepth 1 -exec rm -rf {} +

# Deletes all files in temp_input
find ./api/file_handling/temp_input -mindepth 1 -exec rm -rf {} +

# Deletes the 'weights' folder and its contents
find ./syncnet_python/detectors/s3fd/weights -mindepth 0 -exec rm -rf {} +

# Deletes the 'syncnet_v2.model' file
find ./syncnet_python/data -type f -name 'syncnet_v2.model' -exec rm -f {} + 
