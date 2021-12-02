# import config_util
import encoders_comparison_tool as enc
import numpy as np
import os

options = np.array([["-c:v", "libx264"],
                   ["-level", "4.1"],
                   ["-preset", "veryfast"],
                   ["-crf", enc.sweep_param("add", 10, 11, 1)],
                   ["-an"],
                   ["-sn"]], dtype=object)
options1 = np.array([["-c:v", "libsvtav1"],
                    ["-level", "6.3"],
                    ["-preset", enc.sweep_param("add", 1, 10, 1)]], dtype=object)
options2 = np.array([["-c:v", "libx264"],
                    ["-level", "4.1"],
                    ["-preset", enc.sweep_param("list", ["ultrafast", "medium", "slow"])],
                    ["-b:v", enc.sweep_param("lin", 0.1, 4, 4, "", "M")],
                    ["-an"],
                    ["-y"],
                    ["-t", "0.04"],
                    ["-sn"]], dtype=object)
transcode_set = []
transcode_set = np.append(transcode_set, enc.Transcode_setting("ffmpeg_transcode.py", "/usr/bin/ffmpeg", options))
transcode_set = np.append(transcode_set, enc.Transcode_setting("ffmpeg_transcode.py", "/usr/bin/ffmpeg", options1, concurrent=-1))
transcode_set = np.append(transcode_set, enc.Transcode_setting("ffmpeg_transcode.py", "/usr/bin/ffmpeg", options2, concurrent=1))
binaries = {
    "ffprobe": "/usr/bin/ffprobe"
    }
if os.name == "nt":
    binaries["ffprobe"] = "ffmpeg-n4.4.1-2-gcc33e73618-win64-gpl-4.4/bin/ffprobe.exe"
    for settings in transcode_set:
        settings.binary = "ffmpeg-n4.4.1-2-gcc33e73618-win64-gpl-4.4/bin/ffmpeg.exe"
fileprefix = ""
filesuffix = ".mkv"
inputfiles_gen = (fileprefix + (str(x) + filesuffix) for x in range(1, 2))
inputfiles_list = ["Sintel.2010.720p_30s.mkv", "1.mkv", "2.mkv"]
for f in inputfiles_list:
    print(f)

outputpath = "out/"
if os.path.isdir(outputpath) == 0:
    os.mkdir(outputpath)

print(enc.transcode_check(binaries, inputfiles_list, transcode_set[2]))
#print(enc.transcode_check(binaries, inputfiles_list, transcode_set[2], "slow"))
print(enc.transcode_check(binaries, inputfiles_list, transcode_set[2], "quick", 7))
#print(enc.transcode_check(binaries, inputfiles_list, transcode_set[2], "slow", 7))
print(enc.transcode_check(binaries, inputfiles_list, transcode_set[2]))
print(transcode_set[2]())
print("")
print("encoding:\n")
#enc.transcode(binaries, inputfiles_list, transcode_set[2], outputpath)

