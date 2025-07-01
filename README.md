# subz

`subz` is a simple tool to generate subtitles (`.srt`) from media files using [whisperx](https://github.com/m-bain/whisperX), packaged with docker for portability and GPU acceleration.


## Requirements

- docker
- nvidia-container-toolkit
- [just](https://github.com/casey/just)

## Setup

```bash
git clone https://github.com/jgsch/subz.git
cd subz
```

```bash
just build
```

## Usage

To generate subtitles from a media file (e.g., `.mp4`, `.mkv`):

```bash
just subtitle file.mp4
```

You can also customize parameters:

| Argument      | Description                                              | Example             |
| ------------- | -------------------------------------------------------- | ------------------- |
| `model`       | Whisper model to use  (default: large-v3)                | `model=medium`      | 
| `audio_track` | Audio track index (default: 0)                           | `audio_track=1`     |
| `offset`      | Time offset in seconds (e.g., for sync fix) (default: 0) | `offset=0.5`        |

```
just subtitle file.mp4 model=base audio_track=1 offset=0.5
```
