# syncNet model

mkdir syncnet_python/data
wget http://www.robots.ox.ac.uk/~vgg/software/lipsync/data/syncnet_v2.model -O syncnet_python/data/syncnet_v2.model
wget http://www.robots.ox.ac.uk/~vgg/software/lipsync/data/example.avi -O syncnet_python/data/example.avi

# for the pre-processing pipeline
mkdir syncnet_python/detectors/s3fd/weights
wget https://www.robots.ox.ac.uk/~vgg/software/lipsync/data/sfd_face.pth -O syncnet_python/detectors/s3fd/weights/sfd_face.pth


# ensuring gitignored files are recreated upon cloning
mkdir -p api/logs/final_logs
mkdir -p api/logs/run_logs
mkdir -p api/logs/logs
mkdir -p syncnet_python/file_handling/temp_input
mkdir -p syncnet_python/file_handling/final_output
