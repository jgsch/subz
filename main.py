import argparse
import logging
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, List, Tuple

import ffmpeg
import torch
import whisperx
from faster_whisper.utils import available_models

log = logging.getLogger("subz")


def get_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("file")
    parser.add_argument(
        "--output",
        help="Path to save the output subtitle file.",
    )
    parser.add_argument(
        "--whisper-model",
        choices=available_models(),
        default="large-v3",
        help="Type of Whisper model to use for transcription.",
    )
    parser.add_argument(
        "--audio-track",
        type=int,
        default=0,
        help="Audio track index to extract from the media file.",
    )
    parser.add_argument(
        "--offset",
        type=float,
        default=0.0,
        help="Time offset (in seconds) to apply to the subtitle timestamps.",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose logging for debugging.",
    )
    return parser.parse_args()


def setup_logging():
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s:%(name)s:%(levelname)s - %(message)s",
        datefmt="%H:%M:%S",
    )
    for package in [
        "filelock",
        "fsspec",
        "matplotlib",
        "numba",
        "pytorch_lightning",
        "speechbrain",
        "torio",
        "urllib3",
    ]:
        logging.getLogger(package).propagate = False


def get_segments(
    whisper_model: str,
    audio_path: str,
) -> List[Dict[str, Any]]:
    """
    Transcribe and align audio using WhisperX.

    Args:
        whisper_model (str): Whisper model type (e.g., 'large-v3').
        audio_path (str): Path to the input audio file.

    Returns:
        List[Dict[str, Any]]: List of transcription segments with timing.
    """

    device = "cpu"
    if torch.cuda.is_available():
        device = "cuda"

    log.debug(f"Loading model (name={whisper_model}) on {device}")

    model = whisperx.load_model(
        whisper_model,
        device,
        compute_type="float16" if device == "cuda" else "float32",
    )

    audio = whisperx.load_audio(audio_path)

    log.debug("Transcribe")

    result = model.transcribe(audio)

    log.debug("Align")

    model_a, metadata = whisperx.load_align_model(
        language_code=result["language"],
        device=device,
    )

    result = whisperx.align(
        result["segments"],
        model_a,
        metadata,
        audio,
        device,
        return_char_alignments=False,
    )

    return result["segments"]  # type: ignore


def split_seconds(seconds: float) -> Tuple[int, int, float]:
    """
    Convert seconds into hours, minutes, and remaining seconds.

    Args:
        seconds (float): Time in seconds.

    Returns:
        Tuple[int, int, float]: Hours, minutes, and seconds.
    """
    hours = seconds // 3600
    seconds %= 3600
    minutes = seconds // 60
    seconds %= 60
    return int(hours), int(minutes), seconds


def get_subtitles(segments: List[Dict[str, Any]], offset: float) -> str:
    """
    Convert transcription segments into SRT-formatted subtitles.

    Args:
        segments (List[Dict[str, Any]]): List of transcription segments.
        offset (float): Time offset to apply to subtitle start times.

    Returns:
        str: Subtitle content in SRT format.
    """
    log.debug("Creation of subtitle file")
    subtitles = []
    for idx, segment in enumerate(segments, start=1):
        sh, sm, ss = split_seconds(segment["start"] + offset)
        eh, em, es = split_seconds(segment["end"])
        timestamp = f"{sh}:{sm}:{ss:.3f} --> {eh}:{em}:{es:.3f}"
        timestamp = timestamp.replace(".", ",")
        subtitles += [str(idx), timestamp, segment["text"].strip(), ""]
    return "\n".join(subtitles)


if __name__ == "__main__":
    args = get_args()

    if args.verbose:
        setup_logging()

    src = Path(args.file)
    if not src.is_file():
        raise FileNotFoundError(f"{src} not found")
    log.debug(f"Source: {src}")

    if args.output is None:
        dest = src.parent / src.with_suffix(".srt")
    else:
        dest = Path(args.output)
    log.debug(f"Destination: {dest}")

    start = time.time()
    with tempfile.TemporaryDirectory() as tmp:
        log.debug(f"Extraction of audio (track={args.audio_track})")
        params = {
            "map": f"0:a:{args.audio_track}",
            "acodec": "pcm_s16le",
            "ar": 16000,
            "ac": 2,
            "loglevel": "quiet",
        }
        tmp_dest = Path(tmp) / src.with_suffix(".wav")
        ffmpeg.input(src).output(str(tmp_dest), **params).overwrite_output().run()

        segments = get_segments(args.whisper_model, str(tmp_dest))

        subtitles = get_subtitles(segments, args.offset)
        with open(dest, "w") as f:
            f.write(subtitles)

        print(
            f"Subtitles saved at '{dest}' (done in {int(time.time() - start)} seconds)"
        )
