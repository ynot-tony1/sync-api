import torch

#DEVICE = "cpu"

if torch.cuda.is_available():
   DEVICE = "cuda"
   print("CUDA is enabled. Using GPU:", torch.cuda.get_device_name(torch.cuda.current_device()))
else:
    DEVICE = "cpu"
    print("No CUDA device found. Falling back to CPU.")
