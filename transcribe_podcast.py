#!/usr/bin/env python3

import argparse
import os
import sys
from pathlib import Path
from urllib.parse import urlparse
import requests
from tqdm import tqdm

try:
    import whisper
    if not hasattr(whisper, 'load_model'):
        print("Error: Incorrect whisper package installed. Please install openai-whisper:", file=sys.stderr)
        print("pip install --upgrade --no-deps openai-whisper", file=sys.stderr)
        sys.exit(1)
except ImportError:
    print("Error: whisper not found. Please install openai-whisper:", file=sys.stderr)
    print("pip install openai-whisper", file=sys.stderr)
    sys.exit(1)

def download_audio(url: str, output_path: str) -> bool:
    """
    Download audio file from URL with progress bar
    Returns True if successful, False otherwise
    """
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        # Get file size for progress bar
        total_size = int(response.headers.get('content-length', 0))
        
        # Create progress bar
        progress = tqdm(
            total=total_size,
            unit='iB',
            unit_scale=True,
            desc='Downloading podcast'
        )
        
        # Download with progress
        with open(output_path, 'wb') as file:
            for data in response.iter_content(chunk_size=1024):
                size = file.write(data)
                progress.update(size)
        progress.close()
        
        return True
    except Exception as e:
        print(f"Error downloading file: {str(e)}", file=sys.stderr)
        return False

def get_output_filename(url: str) -> str:
    """Generate output filename from URL"""
    parsed = urlparse(url)
    base_name = os.path.basename(parsed.path)
    name_without_ext = os.path.splitext(base_name)[0]
    return f"{name_without_ext}_transcript.txt"

def transcribe_audio(audio_path: str, output_path: str, model_name: str = "turbo") -> bool:
    """
    Transcribe audio file using Whisper
    Returns True if successful, False otherwise
    """
    try:
        print("Loading Whisper model...")
        model = whisper.load_model(model_name)
        
        print("Transcribing audio... This may take a while.")
        result = model.transcribe(audio_path)
        
        # Save transcript
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(result["text"])
        
        return True
    except Exception as e:
        print(f"Error during transcription: {str(e)}", file=sys.stderr)
        return False

def main():
    parser = argparse.ArgumentParser(description="Download and transcribe a podcast episode")
    parser.add_argument("url", help="URL of the podcast episode (MP3)")
    parser.add_argument("--model", default="turbo", help="Whisper model to use (default: turbo)")
    parser.add_argument("--output", "-o", help="Output file path (optional)")
    args = parser.parse_args()

    # Create output directory if it doesn't exist
    output_dir = Path("transcripts")
    output_dir.mkdir(exist_ok=True)
    
    # Generate output filename if not provided
    output_path = args.output if args.output else output_dir / get_output_filename(args.url)
    
    # Temporary file for downloaded audio
    temp_audio = output_dir / "temp_audio.mp3"
    
    try:
        # Download audio
        print(f"Downloading podcast from {args.url}")
        if not download_audio(args.url, temp_audio):
            sys.exit(1)
        
        # Transcribe
        print(f"Transcribing to {output_path}")
        if not transcribe_audio(str(temp_audio), output_path, args.model):
            sys.exit(1)
        
        print(f"\nTranscription completed successfully!")
        print(f"Transcript saved to: {output_path}")
        
    finally:
        # Clean up temporary file
        if temp_audio.exists():
            temp_audio.unlink()

if __name__ == "__main__":
    main() 