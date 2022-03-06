# encoders-comparison-tool
Tool for batch transcoding video sequences for video encoder comparison.

The tool is under development.

For now it's just smarter Python script. No additional queuing of jobs.

Note:

- For VVenC have prepared YUV file with same name as input video and ".yuv" extension. From input video is retrieved pixel format, size and framerate of video.

### Work in progress

- Minimal Resource Manager - Uncompressed test sequences is large, so storing
them in lightweight ffvhuff or other compressed form on slower disk and on
demand decompres them on faster disk with smaller capacity (RAM or NVMe SSD).
On the RAM will be only one sequence at time and on SSD untill 90% of used space.
For measuring CPU and RAM useage, it's more accurate to work with uncompressed
video because even the ffvhuff adds for 4K content about 700MB of RAM. 
- Support for VVenC/VVdeC
  - usage of resource manager to make YUV files
to just use YUV.
- Dump all the standalone scripts for calculating objective VQM in batch, reading the data
and plotting them with matplotlib. In the future I will integrate them.
- functions for queing, removing, skipping, pausing, stopping and cleaning transcode jobs as a preparation for making something interactive. First will be small TUI.
- Support for xeve/xevd, HM, VTM, AOMenc/dec, VPxenc/dec postponed until I finish other work with more priority (resource manager).

### Task list

- [x] Runs FFmpeg and is able to get stdout, stderr and progress pipe.
- [x] Transcode with progress.
- [x] Batch transcoding using FFmpeg.
- [x] Catching non zero return codes.
- [x] Paralel jobs in batch transcoding.
- [x] Save report from FFmpeg.
- [x] Statistics of CPU and RAM usage through encode process.
- [x] Support for other codecs unsuported by FFmpeg.
- [ ] Resource manager (when not measuring the CPU useage and RAM automatically run more jobs in paralel)
- [ ] Better documentation.

### Ideas

- [ ] Support for MPEG-5 LCEVC if I get hands on encoder/decoder.
- [ ] Objective video quality metrics.
- [ ] Parse output of quality metrics and plot graphs.
- [ ] GUI application or some form of service. REST API or something for server side and PyQt for client application. Suggestions welcome.
- [ ] Loading and saving of configurations for encoder.

## Depencies

FFmpeg (ffmpeg, ffprobe), Python (>= 3.8), NumPy and psutil.

## Usage

In `main.py` is the example of usage.

## Contributing, bug reporting and questions

Have in mind that I am student and relatively new in Python. I may be slow to respond and the code quality is not excellent either.

For now I need to have basic functionality in place and then I will be extending and rewriting core, because the current state is not much readable and comprehensible.

This project is one part of my bachelor thesis about video codecs comparison.
