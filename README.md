# encoders-comparison-tool
Tool for batch transcoding video sequences for video encoder comparison.

### Task list

- [x] Runs FFmpeg and is able to get stdout, stderr and progress pipe.
- [x] Transcode with progress.
- [x] Batch transcoding using FFmpeg.
- [x] Catching non zero return codes.
- [x] Paralel jobs in batch transcoding.
- [ ] Save report from FFmpeg.
- [ ] Documentation
- [ ] Objective video quality metrics.

### Ideas

- [ ] Parse output of quality metrics and plot graphs.
- [ ] Statistics of CPU and RAM usage through encode process.
- [ ] GUI application.
- [ ] Loading and saving of configurations for encoder.
- [ ] Support for other tools unsuported by FFmpeg.

## Depencies

FFmpeg (ffmpeg, ffprobe), Python (>= 3.8) and NumPy

## Usage

In `main.py` is the example of usage.
