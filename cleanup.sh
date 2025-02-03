#!/bin/bash

# deletes all contents of final_output
find ./api/file_handling/final_output -mindepth 1 -exec rm -rf {} +

# deletes all .avi files in data/work
find ./syncnet_python/data -type f -name '*.avi' -exec rm -f {} +

# deletes all pipeline processing files
find ./syncnet_python/data/work -type d -regex '.*/[0-9]+' -exec rm -r {} +

# deletes all final logs
find ./api/logs/final_logs -mindepth 1 -exec rm -rf {} +

# deletes all run logs
find ./api/logs/run_logs -mindepth 1 -exec rm -rf {} +

# deletes all processing logs
find ./api/logs/logs -mindepth 1 -exec rm -rf {} +

# deletes all files in temp_input
find ./api/file_handling/temp_input -mindepth 1 -exec rm -rf {} +
