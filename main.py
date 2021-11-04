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
                   ["-sn"]], dtype=object)
transcode_set = []
transcode_set = np.append(transcode_set, enc.Transcode_setting("ffmpeg_transcode.py", "/usr/bin/ffmpeg", options))
transcode_set = np.append(transcode_set, enc.Transcode_setting("ffmpeg_transcode.py", "ffmpeg", options1))
transcode_set = np.append(transcode_set, enc.Transcode_setting("ffmpeg_transcode.py", "ffmpeg", options2))
binaries = {
    "ffprobe": "/usr/bin/ffprobe"
    }

print(transcode_set[2]())
print("encoding:\n")
enc.transcode(binaries, "t.mkv", transcode_set[2], "out.mkv") #TODO
