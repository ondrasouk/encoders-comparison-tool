import os
import subprocess


top_dir = "/run/media/ondra/video/test3/av1/"

psnr_suffix = "-psnr_logfile.txt"
ssim_suffix = "-ssim_logfile.txt"
vmaf_suffix = "-vmaf_logfile.txt"
# vmaf_model_path = "/home/ondra/Sync/Bakalářka/util/vmaf_4k_v0.6.1.json"
vmaf_model_path = "/home/ondra/Sync/Bakalářka/util/vmaf_v0.6.1.json"
ffmpeg_path = "ffmpeg"


sequences_4k = {
    "Netflix Aerial yuv420p10le 60fps": "/run/media/ondra/SSHD/videa2/used_sequences/Netflix_Aerial_4096x2160_60fps_10bit_420.mkv",
    "ShakeNDry yuv420p 30fps": "/run/media/ondra/SSHD/videa2/used_sequences/ShakeNDry_3840x2160.mkv",
    "SunBath yuv420p10le 50fps": "/run/media/ondra/SSHD/videa2/used_sequences/SunBath_3840x2160_50fps_10bit.mkv",
    "Tree Shade yuv420p10le 30fps": "/run/media/ondra/SSHD/videa2/used_sequences/Tree_Shade_3840x2160_30fps_10bit_yuv420.mkv",
    "Sintel2 yuv420p10le 24fps": "/run/media/ondra/SSHD/videa2/used_sequences/Sintel2_4096x1744_24fps_10bit_420.mkv",
}

sequences = {
    "Netflix Aerial yuv420p10le 60fps": "/run/media/ondra/SSHD/videa2/used_sequences/Netflix_Aerial_2048x1080_60fps_10bit_420.mkv",
    "ShakeNDry yuv420p 30fps": "/run/media/ondra/SSHD/videa2/used_sequences/ShakeNDry_1920x1080.mkv",
    "SunBath yuv420p10le 50fps": "/run/media/ondra/SSHD/videa2/used_sequences/SunBath_1920x1080_50fps_10bit.mkv",
    "Tree Shade yuv420p10le 30fps": "/run/media/ondra/SSHD/videa2/used_sequences/Tree_Shade_1920x1080_30fps_10bit_yuv420.mkv",
    "Sintel2 yuv420p10le 24fps": "/run/media/ondra/SSHD/videa2/used_sequences/Sintel2_2048x872_24fps_10bit_420.mkv",
}

class VideoFileToVQA:
    def __init__(self, videofiles_path):
        self.videofiles_path = videofiles_path
        k = sequences.keys()
        for s in k:
            if s in videofiles_path:
                self.sequence = s
        self.reference = sequences[self.sequence]
        self.mainname = videofiles_path[:-4]
        self.psnr_logfile = self.mainname + psnr_suffix
        self.ssim_logfile = self.mainname + ssim_suffix
        self.vmaf_logfile = self.mainname + vmaf_suffix
        lavfi_str = "ssim=stats_file=" + self.ssim_logfile + ";[0:v][1:v]psnr=stats_file=" + self.psnr_logfile + ";[0:v][1:v]libvmaf=model_path=" + vmaf_model_path + ":log_path=" + self.vmaf_logfile + ":log_fmt=csv:n_threads=6:psnr=1:ms_ssim=1:ssim=1"
        self.cmd = ["chrt", "-i", "0", ffmpeg_path, "-i", self.videofiles_path, "-i", self.reference, "-lavfi", lavfi_str, "-f", "null", "-"]


videofiles_paths = []
videofiles = []

for directory in os.walk(top_dir):
    if directory[2] != []:
        for f in directory[2]:
            if f.endswith(".mkv") and not os.path.exists(os.path.join(directory[0], f[:-4] + "-vmaf_logfile.txt")):
                videofiles_paths.append(os.path.join(directory[0], f))

print(videofiles_paths)

for video in videofiles_paths:
    videofiles.append(VideoFileToVQA(video))

for video in videofiles:
    subprocess.run(video.cmd)



