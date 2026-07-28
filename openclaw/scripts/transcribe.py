#!/usr/bin/env python3
"""
Transcribe audio files using Moonshine Voice (on-device ASR).
Optimized for N100 CPU — uses the Tiny model (34M params).

Usage:
    uv run scripts/transcribe.py <audio_file> [--language en]

Telegram voice notes arrive as OGG/Opus. This script:
1. Converts OGG/Opus → WAV (16kHz mono 16-bit) via ffmpeg
2. Transcribes using Moonshine's Transcriber API
3. Prints the transcript to stdout

Dependencies (inline PEP 723):
    - moonshine-voice (ASR model)
    - wave (stdlib, for WAV handling)

The Tiny model downloads on first use (~50MB) and caches in
~/.cache/moonshine_voice/.
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
                "-ar", "16000",      # 16kHz sample rate (Moonshine requirement)
                "-ac", "1",          # Mono
                "-acodec", "pcm_s16le",  # 16-bit PCM
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
    """Transcribe a WAV file using Moonshine Voice."""
    import wave

    # Read WAV file
    with wave.open(wav_path, "rb") as wf:
        frames = wf.readframes(wf.getnframes())
        sample_rate = wf.getframerate()
        n_channels = wf.getnchannels()
        sampwidth = wf.getsampwidth()

    if sample_rate != 16000:
        print(f"Warning: expected 16kHz, got {sample_rate}Hz", file=sys.stderr)
    if n_channels != 1:
        print(f"Warning: expected mono, got {n_channels} channels", file=sys.stderr)

    # Convert to Moonshine audio format
    # Moonshine expects float32 samples in [-1.0, 1.0]
    import struct
    samples = struct.unpack(f"<{len(frames)//2}h", frames)
    audio_data = [s / 32768.0 for s in samples]

    # Use Moonshine's Transcriber
    from moonshine_voice import Transcriber, Stream
    from moonshine_voice.moonshine_api import get_model_for_language

    model_path, model_arch = get_model_for_language(language)

    transcriber = Transcriber(
        model_path=model_path,
        model_arch=model_arch,
    )

    stream = transcriber.create_stream()
    stream.add_audio(audio_data)
    stream.end_stream()

    # Wait for result
    transcript_lines = []
    while True:
        event = stream.next_event()
        if event is None:
            break
        if hasattr(event, 'text') and event.text:
            transcript_lines.append(event.text)

    return " ".join(transcript_lines).strip()


def main():
    parser = argparse.ArgumentParser(description="Transcribe audio with Moonshine (on-device ASR)")
    parser.add_argument("audio_file", help="Path to audio file (OGG, WAV, MP3, etc.)")
    parser.add_argument("--language", default="en", help="Language code (default: en)")
    parser.add_argument("--keep-wav", action="store_true", help="Keep intermediate WAV file")
    args = parser.parse_args()

    if not os.path.exists(args.audio_file):
        print(f"Error: file not found: {args.audio_file}", file=sys.stderr)
        sys.exit(1)

    input_path = Path(args.audio_file)

    # Check if already WAV at correct format
    needs_conversion = True
    if input_path.suffix.lower() == ".wav":
        needs_conversion = False

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
            os.unlink(wav_path)


if __name__ == "__main__":
    main()
