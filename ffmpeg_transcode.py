import subprocess
import os
import encoders_comparison_tool as enc


def transcode_cmd(binpath, filename, args, outputfile, progress_p_w=4):
    cmd = [binpath, "-i", filename, "-y", "-progress", str("pipe:" + str(progress_p_w))] + list(args) + [outputfile]
    return cmd


def transcode_start(binpath, filename, args, outputfile, ffprobepath):
    progress_p_r, progress_p_w = os.pipe()
    cmd = transcode_cmd(binpath, filename, args, outputfile, progress_p_w)
    process = subprocess.Popen(
        cmd,
        pass_fds=[progress_p_w],
        text=True
    )
    fdr = os.fdopen(progress_p_r)
    fdw = os.fdopen(progress_p_w)
    # Call back into encoders_comparison_tool because the freezed libraries
    # (loaded with importlib) can't make a thread or process.
    return process, fdr, fdw


def transcode_clean(fdw, fdr):
    fdr.close()
    fdw.close()


def transcode_get_info_stop(fdw, fdr):
    transcode_clean(fdw, fdr)


def transcode_get_info(process, fdr):
    print("transcodeGetInfo started.")
    for line in fdr:
        print(line.rstrip("\n"))
        if line == "progress=end":
            break
