import subprocess
import os
import re
import encoders_comparison_tool as enc


def transcode_cmd(binpath, filename, args, outputfile, progress_p_w=4):
    cmd = [binpath, "-i", filename, "-y", "-progress", str("pipe:" + str(progress_p_w))] + list(args) + [outputfile]
    return cmd


def transcode_start(binpath, filename, args, outputfile, ffprobepath):
    fdr, fdw = os.pipe()
    cmd = transcode_cmd(binpath, filename, args, outputfile, fdw)
    process = subprocess.Popen(
        cmd,
        pass_fds=[fdw],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    fdr_open = os.fdopen(fdr)
    # Call back into encoders_comparison_tool because the freezed libraries
    # (loaded with importlib) can't make a thread or process.
    return process, fdr_open, fdr, fdw


def transcode_clean(fdr, fdw):
    try:
        os.close(fdw)
    except OSError:
        pass
    try:
        os.close(fdr)
    except OSError:
        pass


def transcode_get_info_stop(fdr, fdw):
    transcode_clean(fdr, fdw)


def transcode_get_info(process, fdr):
    print("transcodeGetInfo started.")
    for line in fdr:
        print(line.rstrip("\n"))
        if line == "progress=end\n":
            break
        stat = re.sub(r"[\n\t\s]*", "", line).rsplit("=")
        if stat[0] == "speed":
            print(stat[0] + ": " + stat[1].rstrip("x"))
        elif stat[0] == "frame":
            print(stat[0] + ": " + stat[1])
