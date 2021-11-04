import subprocess
import os
import sys
import encoders_comparison_tool as enc


def transcode_cmd(binpath, filename, args, outputfile, progress_p_w=4):
    cmd = [binpath, "-i", filename, "-y", "-progress", str("pipe:" + str(progress_p_w))] + list(args) + [outputfile]
    return cmd


def transcode_start(binpath, filename, args, outputfile, ffprobepath):
    n_frames = enc.video_frames(ffprobepath, filename)
    progress_p_r, progress_p_w = os.pipe()
    cmd = transcode_cmd(binpath, filename, args, outputfile, progress_p_w)
    result = subprocess.Popen(
        cmd,
        pass_fds=[progress_p_w],
        text=True
    )
    try:
        for line in os.fdopen(progress_p_r):
            print(line.rstrip("\n")) # Print output from ffmpeg 
            transcode_get_info(line, n_frames)
            if "progress=end" in line:
                break
    except ValueError:
        os.close(progress_p_w)
        os.close(progress_p_r)
        raise ValueError(result.stderr.rstrip("\n"))


def transcode_get_info(line, n_frames):
    pass
