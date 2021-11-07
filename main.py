# import config_util
import encoders_comparison_tool as enc
import numpy as np

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
                    ["-preset", "ultrafast"],
                    ["-crf", enc.sweep_param("add", 20, 21, 1)],
                    ["-an"],
                    ["-y"],
                    ["-sn"]], dtype=object)
transcode_set = []
transcode_set = np.append(transcode_set, enc.Transcode_setting("ffmpeg_transcode.py", "/usr/bin/ffmpeg", options))
transcode_set = np.append(transcode_set, enc.Transcode_setting("ffmpeg_transcode.py", "ffmpeg", options1, concurrent=-1))
transcode_set = np.append(transcode_set, enc.Transcode_setting("ffmpeg_transcode.py", "ffmpeg", options2, concurrent=2))
binaries = {
    "ffprobe": "/usr/bin/ffprobe"
    }
fileprefix = ""
filesuffix = ".mkv"
inputfiles_gen = (fileprefix + (str(x) + filesuffix) for x in range(1, 2))
inputfiles_list = ["1.mkv", "2.mkv"]
for f in inputfiles_list:
    print(f)

print(transcode_set[2]())
print("encoding:\n")
enc.transcode(binaries, inputfiles_list, transcode_set[2], "out.mkv")
# TODO Make possible to pass an File_parameter class object that works as list
#      or as generator for many names. Eg. 1.mkv, 2.mkv,...
#      For input files and output files.
