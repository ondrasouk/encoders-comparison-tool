import subprocess
import os
import re
import encoders_comparison_tool as enc


def transcode_cmd(binpath, filename, args, outputfile, progress_p_w=4):
    cmd = [binpath, "-i", filename, "-nostdin", "-progress", str("pipe:" + str(progress_p_w))] + list(args) + [outputfile]
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
    # Call back into encoders_comparison_tool because the freezed libraries
    # (loaded with importlib) can't make a new thread or process.
    return process, fdr, fdw


def transcode_clean(fdr, fdw):
    try:
        os.close(fdw)
    except OSError:
        pass
    try:
        os.close(fdr)
    # OSError means the file descriptor is either locked, blocked or not existing (closed)
    # TODO Maybe test with fstat if the FD is closed or blocked?
    # https://stackoverflow.com/questions/6916033/check-if-file-descriptor-is-valid
    except OSError:
        pass


def transcode_get_info_stop(fdr, fdw):
    transcode_clean(fdr, fdw)


def transcode_get_info(process, fdr):
    print("transcodeGetInfo started.")
    fdr_open = os.fdopen(fdr)
    for line in fdr_open:
        if line == "progress=end\n":
            break
        stat = re.sub(r"[\n\t\s]*", "", line).rsplit("=")
        if stat[0] == "speed":
            print(stat[0] + ": " + stat[1].rstrip("x"))
        elif stat[0] == "frame":
            print(stat[0] + ": " + stat[1])
        elif stat[0] == "fps":
            print(stat[0] + ": " + stat[1])
