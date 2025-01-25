# SyncNet model

mkdir data
wget http://www.robots.ox.ac.uk/~vgg/software/lipsync/data/syncnet_v2.model -O data/syncnet_v2.model
wget http://www.robots.ox.ac.uk/~vgg/software/lipsync/data/example.avi -O data/example.avi

# For the pre-processing pipeline
mkdir detectors/s3fd/weights
wget https://www.robots.ox.ac.uk/~vgg/software/lipsync/data/sfd_face.pth -O detectors/s3fd/weights/sfd_face.pth

mkdir -p logs/final_logs
mkdir -p logs/run_logs
mkdir -p logs/logs
mkdir -p file_handling/temp_input
mkdir -p file_handling/final_output
