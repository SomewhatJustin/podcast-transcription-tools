# Podcast Transcription Tools

A collection of tools for searching, downloading, and transcribing podcasts using OpenAI's Whisper model with GPU acceleration.

## Prerequisites

- Linux system with an AMD GPU
- ROCm-compatible GPU (most modern AMD GPUs)
- Docker installed
- Docker Compose installed
- Docker user permissions (user added to `docker` group)

## GPU Setup with Docker

### For RDNA 3 GPUs (RX 7000 series)

You can use either Docker Compose (recommended) or plain Docker commands.

#### Option 1: Using Docker Compose

1. Install Docker and Docker Compose:
```bash
sudo apt install docker.io docker-compose
sudo usermod -aG docker $USER  # Log out and back in after this
```

2. Start the container:
```bash
docker-compose up -d  # Start in detached mode
docker-compose exec transcribe bash  # Connect to the container
```

The container will automatically install ffmpeg during startup.

3. Inside the container, verify GPU detection:
```bash
cd /workspace
python3 test.py
```

4. Install requirements and run transcription:
```bash
pip install -r requirements.txt
python3 transcribe_podcast.py --model base <MP3_URL>
```

All outputs (transcripts, downloaded files, etc.) will be saved in your project directory on your host system. The container's `/workspace` directory is directly mapped to your project folder, so any files created or modified inside the container will persist on your system.

Default output locations:
- Transcripts: `./transcripts/` directory
- Downloaded audio: Temporary files in `./transcripts/` (automatically cleaned up)
- Model cache: `$HOME/.cache` (persisted between container runs)

To stop the container:
```bash
docker-compose down
```

#### Option 2: Using Docker Directly

1. Install Docker:
```bash
sudo apt install docker.io
sudo usermod -aG docker $USER  # Log out and back in after this
```

2. Pull the specific ROCm PyTorch image that matches your system:
```bash
docker pull rocm/pytorch:rocm6.3_ubuntu22.04_py3.10_pytorch_release_2.3.0
```

3. Run the container with GPU support and install ffmpeg:
```bash
docker run -it \
  --device=/dev/kfd \
  --device=/dev/dri \
  --group-add video \
  --ipc=host \
  --shm-size 16G \
  -v $(pwd):/workspace \
  -v $HOME/.cache:/root/.cache \
  -e HSA_OVERRIDE_GFX_VERSION=11.0.0 \
  -e PYTORCH_ROCM_ARCH=gfx1100 \
  -e AMD_SERIALIZE_KERNEL=3 \
  -e TORCH_USE_HIP_DSA=1 \
  rocm/pytorch:rocm6.3_ubuntu22.04_py3.10_pytorch_release_2.3.0 \
  bash -c "apt-get update && apt-get install -y ffmpeg && bash"
```

4. Inside the container, verify GPU detection:
```bash
# Create a test.py file with the following content:
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

# Run the test
python3 test.py
```

5. Install requirements and run transcription:
```bash
cd /workspace
pip install -r requirements.txt
python3 transcribe_podcast.py --model base <MP3_URL>
```

## Usage

### Search for Podcasts
```bash
python3 podcast_search.py
```

### Transcribe Episodes
```bash
python3 transcribe_podcast.py --model base <MP3_URL>
```

Options:
- `--model`: Whisper model to use (default: base)
- `--output`: Output file path (optional)

## Environment Variables

For RDNA 3 GPUs (RX 7000 series), the following environment variables are important:

- `HSA_OVERRIDE_GFX_VERSION=11.0.0`: Sets the correct GFX version for RDNA 3
- `PYTORCH_ROCM_ARCH=gfx1100`: Specifies the GPU architecture
- `AMD_SERIALIZE_KERNEL=3`: Helps with kernel serialization
- `TORCH_USE_HIP_DSA=1`: Enables direct shared access for HIP

## Troubleshooting

### 1. Verify GPU Detection
You can verify GPU detection using the provided `test.py` script. Expected output should show:
- Python version
- PyTorch version
- ROCm availability (should be True)
- GPU Device name (e.g., "AMD Radeon™ RX 7600 XT")
- GPU Count (should be 1 or more)
- Current device (usually 0)

### 2. Common Issues

#### GPU Not Detected
- Verify ROCm installation: `rocm-smi`
- Check GPU compatibility: `rocminfo | grep gfx`
- Make sure you're using the correct Docker image for your GPU
- Verify all required devices are mounted (--device=/dev/kfd --device=/dev/dri)

#### Memory Issues
- The container is configured with 16GB shared memory (--shm-size 16G)
- Try using a smaller model (--model tiny or --model base)
- Reduce batch size if needed

#### HIP/ROCm Errors
- Make sure environment variables are set correctly for your GPU
- Try using a different model size
- Check ROCm version compatibility
- Verify GPU architecture settings

#### Known Warnings

1. Memory-Efficient Attention Warning:
```
UserWarning: Torch was not compiled with memory efficient attention...
```
This warning appears because the ROCm version of PyTorch doesn't include memory-efficient attention optimizations. This is normal and won't affect functionality, but might slightly impact memory usage. If you encounter memory issues:
- Try using a smaller model (tiny or base)
- Increase shared memory (--shm-size)
- Process shorter audio segments

### 3. Version Compatibility

For RDNA 3 GPUs (RX 7000 series):
- Use ROCm 6.3 or later
- Use PyTorch 2.3.0 or later
- Set GFX version to 11.0.0
- Use architecture gfx1100

## Notes

- The container mounts your current directory as `/workspace`
- Model downloads are cached in `$HOME/.cache`
- First-time runs will download the Whisper model
- For RDNA 3 GPUs, the base model is recommended for initial testing
- Consider using the tiny model if you encounter memory issues

## Quick Test Command

To test everything in one command:
```bash
docker run -it --device=/dev/kfd --device=/dev/dri --group-add video --ipc=host --shm-size 16G \
  -v $(pwd):/workspace -v $HOME/.cache:/root/.cache \
  -e HSA_OVERRIDE_GFX_VERSION=11.0.0 -e PYTORCH_ROCM_ARCH=gfx1100 \
  -e AMD_SERIALIZE_KERNEL=3 -e TORCH_USE_HIP_DSA=1 \
  rocm/pytorch:rocm6.3_ubuntu22.04_py3.10_pytorch_release_2.3.0 \
  bash -c "cd /workspace && python3 test.py"
``` 