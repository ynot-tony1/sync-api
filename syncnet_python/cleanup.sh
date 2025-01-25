#!/bin/bash

# deletes all contents of final_output
find ./file_handling/final_output -mindepth 1 -exec rm -rf {} +

# deletes all .avi files in data/work
find ./data -type f -name '*.avi' -exec rm -f {} +

# deletes all pipeline processing files
find ./data/work -type d -regex '.*/[0-9]+' -exec rm -r {} +

# deletes all final logs
find ./logs/final_logs -mindepth 1 -exec rm -rf {} +

# deletes all run logs
find ./logs/run_logs -mindepth 1 -exec rm -rf {} +

# deletes all processing logs
find ./logs/logs -mindepth 1 -exec rm -rf {} +

# deletes all files in temp_input
find ./file_handling/temp_input -mindepth 1 -exec rm -rf {} +
