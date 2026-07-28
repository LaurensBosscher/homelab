#!/usr/bin/env python3
"""
Local Moonshine transcription server — OpenAI Whisper API compatible.

Exposes a POST /v1/audio/transcriptions endpoint that accepts audio files
and returns transcripts using Moonshine Voice (on-device ASR).

Optimized for N100 CPU — uses the Tiny model (34M params, ~69ms latency).

Usage:
    uv run scripts/transcribe_server.py [--host 127.0.0.1] [--port 8765]

The server loads the model on first request and caches it in memory.
Subsequent transcriptions are fast (~0.5-2s for typical voice notes).
"""

# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "moonshine-voice",
#     "aiohttp",
# ]
# ///

import argparse
import asyncio
import io
import logging
import os
import struct
import tempfile
import wave
from aiohttp import web, ClientSession

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("moonshine-server")

# Lazy-loaded globals
_transcriber = None
_model_path = None
_model_arch = None


def get_transcriber(language: str = "en"):
    """Lazy-load the Moonshine transcriber on first use."""
    global _transcriber, _model_path, _model_arch
    if _transcriber is None:
        from moonshine_voice import Transcriber
        from moonshine_voice.moonshine_api import get_model_for_language
        log.info("Loading Moonshine model for language='%s'...", language)
        _model_path, _model_arch = get_model_for_language(language)
        log.info("Model path: %s, arch: %s", _model_path, _model_arch)
        _transcriber = Transcriber(model_path=_model_path, model_arch=_model_arch)
        log.info("Moonshine model loaded successfully")
    return _transcriber


async def convert_to_wav(input_data: bytes, input_format: str = "ogg") -> bytes:
    """Convert audio bytes to 16kHz mono 16-bit WAV using ffmpeg."""
    with tempfile.NamedTemporaryFile(suffix=f".{input_format}", delete=False) as infile:
        infile.write(input_data)
        infile_path = infile.name

    outfile_path = infile_path.rsplit(".", 1)[0] + ".wav"

    proc = await asyncio.create_subprocess_exec(
        "ffmpeg", "-y", "-i", infile_path,
        "-ar", "16000", "-ac", "1", "-acodec", "pcm_s16le",
        "-loglevel", "error",
        outfile_path,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    _, stderr = await proc.communicate()

    os.unlink(infile_path)
    if proc.returncode != 0:
        err = stderr.decode() if stderr else "unknown"
        raise RuntimeError(f"ffmpeg failed: {err}")

    with open(outfile_path, "rb") as f:
        wav_data = f.read()
    os.unlink(outfile_path)
    return wav_data


def transcribe_wav(wav_bytes: bytes, language: str = "en") -> str:
    """Transcribe WAV bytes using Moonshine."""
    transcriber = get_transcriber(language)

    # Parse WAV
    with wave.open(io.BytesIO(wav_bytes), "rb") as wf:
        frames = wf.readframes(wf.getnframes())
        sample_rate = wf.getframerate()

    if sample_rate != 16000:
        log.warning("Expected 16kHz, got %dHz", sample_rate)

    # Convert to float32 [-1.0, 1.0]
    samples = struct.unpack(f"<{len(frames)//2}h", frames)
    audio_data = [s / 32768.0 for s in samples]

    # Transcribe
    stream = transcriber.create_stream()
    stream.add_audio(audio_data)
    stream.end_stream()

    transcript_lines = []
    while True:
        event = stream.next_event()
        if event is None:
            break
        if hasattr(event, 'text') and event.text:
            transcript_lines.append(event.text)

    return " ".join(transcript_lines).strip()


async def handle_transcriptions(request: web.Request) -> web.Response:
    """OpenAI-compatible POST /v1/audio/transcriptions endpoint."""
    log.info("Transcription request from %s", request.remote)

    reader = await request.multipart()
    audio_data = None
    filename = "audio.ogg"
    language = "en"

    async for field in reader:
        if field.name == "file":
            audio_data = await field.read(decode=False)
            filename = field.filename or "audio.ogg"
        elif field.name == "language":
            language = (await field.text()).strip() or "en"
        elif field.name == "model":
            pass  # Ignore model name — we always use Moonshine

    if audio_data is None:
        return web.json_response({"error": {"message": "No audio file provided"}}, status=400)

    # Detect format from filename
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else "ogg"
    if ext == "wav":
        wav_bytes = audio_data
    else:
        try:
            wav_bytes = await convert_to_wav(audio_data, ext)
        except RuntimeError as e:
            log.error("Audio conversion failed: %s", e)
            return web.json_response({"error": {"message": str(e)}}, status=500)

    try:
        loop = asyncio.get_event_loop()
        transcript = await loop.run_in_executor(None, transcribe_wav, wav_bytes, language)
    except Exception as e:
        log.error("Transcription failed: %s", e, exc_info=True)
        return web.json_response({"error": {"message": f"Transcription failed: {e}"}}, status=500)

    log.info("Transcribed %s (%d bytes) → %d chars", filename, len(audio_data), len(transcript))

    # OpenAI-compatible response format
    return web.json_response({"text": transcript})


async def handle_health(request: web.Request) -> web.Response:
    """Health check endpoint."""
    return web.json_response({"status": "ok", "model_loaded": _transcriber is not None})


def main():
    parser = argparse.ArgumentParser(description="Moonshine local transcription server")
    parser.add_argument("--host", default="127.0.0.1", help="Bind host (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8765, help="Bind port (default: 8765)")
    args = parser.parse_args()

    app = web.Application(client_max_size=50 * 1024 * 1024)  # 50MB limit
    app.router.add_post("/v1/audio/transcriptions", handle_transcriptions)
    app.router.add_post("/audio/transcriptions", handle_transcriptions)  # Alt path
    app.router.add_get("/health", handle_health)

    log.info("Starting Moonshine transcription server on %s:%d", args.host, args.port)
    log.info("Model will load on first transcription request")
    web.run_app(app, host=args.host, port=args.port, print=None)


if __name__ == "__main__":
    main()
