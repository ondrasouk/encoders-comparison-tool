# encoders-comparison-tool
Tool for batch transcoding video sequences for video encoder comparison.

### Task list

- [x] Runs FFmpeg and is able to get stdout, stderr and progress pipe.
- [x] Transcode with progress.
- [x] Batch transcoding using FFmpeg.
- [x] Catching non zero return codes.
- [x] Paralel jobs in batch transcoding.
- [x] Save report from FFmpeg.
- [x] Statistics of CPU and RAM usage through encode process.
- [ ] Support for other codecs unsuported by FFmpeg.
- [ ] Better documentation.

### Ideas

- [ ] Objective video quality metrics.
- [ ] Parse output of quality metrics and plot graphs.
- [ ] GUI application.
- [ ] Loading and saving of configurations for encoder.

## Depencies

FFmpeg (ffmpeg, ffprobe), Python (>= 3.8), NumPy and psutil

## Usage

In `main.py` is the example of usage.
