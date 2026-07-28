#!/usr/bin/env python3
"""
Transcribe audio files using Moonshine Voice CLI (on-device ASR).
Optimized for N100 CPU — uses the Tiny model (34M params).

Usage:
    uv run scripts/transcribe.py <audio_file> [--language en]

Handles any audio format ffmpeg supports (OGG/Opus, MP3, WAV, M4A, etc.).
Converts to 16kHz mono WAV, then calls moonshine-voice transcribe.

Dependencies (inline PEP 723): none beyond stdlib + moonshine-voice.
ffmpeg must be installed system-wide.
"""

# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "moonshine-voice",
# ]
# ///

import argparse
import subprocess
import sys
import tempfile
import os
from pathlib import Path


def convert_to_wav(input_path: str, output_path: str) -> bool:
    """Convert any audio format to 16kHz mono 16-bit WAV using ffmpeg."""
    try:
        subprocess.run(
            [
                "ffmpeg", "-y", "-i", input_path,
                "-ar", "16000",
                "-ac", "1",
                "-acodec", "pcm_s16le",
                "-loglevel", "error",
                output_path,
            ],
            check=True,
            capture_output=True,
        )
        return True
    except subprocess.CalledProcessError as e:
        print(f"ffmpeg error: {e.stderr.decode() if e.stderr else e}", file=sys.stderr)
        return False
    except FileNotFoundError:
        print("ffmpeg not found. Install with: apt-get install ffmpeg", file=sys.stderr)
        return False


def transcribe_wav(wav_path: str, language: str = "en") -> str:
    """Transcribe a WAV file using the moonshine-voice CLI."""
    try:
        result = subprocess.run(
            [
                "moonshine-voice", "transcribe",
                "--language", language,
                wav_path,
            ],
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode != 0:
            print(f"moonshine-voice error: {result.stderr}", file=sys.stderr)
            return ""
        return result.stdout.strip()
    except FileNotFoundError:
        print("moonshine-voice not found. Install with: uv pip install moonshine-voice", file=sys.stderr)
        return ""
    except subprocess.TimeoutExpired:
        print("Transcription timed out after 120s", file=sys.stderr)
        return ""


def main():
    parser = argparse.ArgumentParser(description="Transcribe audio with Moonshine (on-device ASR)")
    parser.add_argument("audio_file", help="Path to audio file (OGG, WAV, MP3, M4A, etc.)")
    parser.add_argument("--language", default="en", help="Language code (default: en)")
    parser.add_argument("--keep-wav", action="store_true", help="Keep intermediate WAV file")
    args = parser.parse_args()

    if not os.path.exists(args.audio_file):
        print(f"Error: file not found: {args.audio_file}", file=sys.stderr)
        sys.exit(1)

    input_path = Path(args.audio_file)
    needs_conversion = input_path.suffix.lower() != ".wav"

    if needs_conversion:
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            wav_path = tmp.name
        print(f"Converting {input_path.name} → WAV...", file=sys.stderr)
        if not convert_to_wav(str(input_path), wav_path):
            sys.exit(1)
    else:
        wav_path = str(input_path)

    try:
        print(f"Transcribing with Moonshine (language={args.language})...", file=sys.stderr)
        transcript = transcribe_wav(wav_path, args.language)
        print(transcript)
    finally:
        if needs_conversion and not args.keep_wav:
            try:
                os.unlink(wav_path)
            except OSError:
                pass


if __name__ == "__main__":
    main()
