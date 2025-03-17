import torch
import sys

print("Python version:", sys.version)
print("PyTorch version:", torch.__version__)
print("ROCm available:", torch.cuda.is_available())
if torch.cuda.is_available():
    print("GPU Device:", torch.cuda.get_device_name(0))
    print("GPU Count:", torch.cuda.device_count())
    print("Current device:", torch.cuda.current_device())
else:
    print("No GPU detected")
