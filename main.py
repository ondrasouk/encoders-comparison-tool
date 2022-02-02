import os
import numpy as np
import encoders_comparison_tool as enc

# Options for transcoder
# One line is one option
# enc.sweep_param is class for defining variable in that position
options = np.array([["-c:v", "libx264"],
                   ["-level", "4.1"],
                   ["-preset", "veryfast"],
                   ["-crf", enc.sweep_param("add", 10, 11, 1)],
                   ["-an"],
                   ["-sn"]], dtype=object)
options1 = np.array([["-c:v", "libsvtav1"],
                    ["-level", "6.3"],
                    ["-preset", enc.sweep_param("add", 9, 10, 1)]], dtype=object)
options2 = np.array([["-c:v", "libx264"],
                    ["-level", "4.1"],
                    ["-preset", enc.sweep_param("list", ["ultrafast", "medium", "slow"])],
                    ["-b:v", enc.sweep_param("lin", 0.1, 4, 2, "", "M")],
                    ["-an"],
                    ["-y"],
                    ["-sn"]], dtype=object)
# Make transcode_set list (options list).
# enc.Transcode_setting is class for making transcode options with what module
# to load and what binary it will use.
transcode_set = []
transcode_set = np.append(transcode_set, enc.Transcode_setting("ffmpeg_transcode.py", "/usr/bin/ffmpeg", options))
transcode_set = np.append(transcode_set, enc.Transcode_setting("ffmpeg_transcode.py", "/usr/bin/ffmpeg", options1, concurrent=-1))
transcode_set = np.append(transcode_set, enc.Transcode_setting("ffmpeg_transcode.py", "/usr/bin/ffmpeg", options2, concurrent=1))
# Dictionary for storing paths for binaries.
binaries = {
    "ffprobe": "/usr/bin/ffprobe"
    "ffmpeg": "/usr/bin/ffmpeg"
    }
# Settings for Windows testing.
if os.name == "nt":
    binaries["ffprobe"] = "ffmpeg-n4.4.1-2-gcc33e73618-win64-gpl-4.4/bin/ffprobe.exe"
    binaries["ffmpeg"] = "ffmpeg-n4.4.1-2-gcc33e73618-win64-gpl-4.4/bin/ffmpeg.exe"
    for settings in transcode_set:
        settings.binary = "ffmpeg-n4.4.1-2-gcc33e73618-win64-gpl-4.4/bin/ffmpeg.exe"
# Input video files can be stored as strings in iterable
# object (list, touples, generators, ...)
fileprefix = ""
filesuffix = ".mkv"
inputfiles_gen = (fileprefix + (str(x) + filesuffix) for x in range(1, 2))
inputfiles_list = ["Sintel.2010.720p_30s.mkv", "1.mkv", "2.mkv"]

# Output directory for encoded videosequences
outputpath = "out/"
if os.path.isdir(outputpath) == 0:
    os.mkdir(outputpath)

# Test configuration for errors before running encode
print(enc.transcode_check(binaries, inputfiles_list, transcode_set[2]))
print(enc.transcode_check(binaries, inputfiles_list, transcode_set[2], "slow"))
# Print used configuration.
print(transcode_set[2]())
print("\nencoding:\n")
# Start the transcode.
enc.transcode(binaries, inputfiles_list, transcode_set[2], outputpath)
