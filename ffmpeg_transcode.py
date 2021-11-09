import subprocess
import os
import re
import encoders_comparison_tool as enc


frame_num = 1


# Internal function
def transcode_cmd(binpath, filename, args, outputfile, progress_p_w=4):
    cmd = [binpath, "-i", filename, "-nostdin", "-progress", str("pipe:" + str(progress_p_w))] + list(args) + [outputfile]
    return cmd


# Start transcode
def transcode_start(binpath, filename, args, outputfile, ffprobepath):
    fdr, fdw = os.pipe()
    cmd = transcode_cmd(binpath, filename, args, outputfile, fdw)
    global frame_num
    frame_num = enc.video_frames(ffprobepath, filename)
    print(frame_num)
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


# Clean after transcode ended.
def transcode_clean(fdr, fdw):
    try:
        os.close(fdw)
    except OSError:
        pass
    try:
        os.close(fdr)
    # OSError means the file descriptor is either locked, blocked or not existing (closed)
    # TODO Maybe test with fstat if the FD is closed or blocked and if blocked raise error
    # https://stackoverflow.com/questions/6916033/check-if-file-descriptor-is-valid
    except OSError:
        pass


# Optional: If the transcode_get_info has the risk of stuck implement this function.
def transcode_get_info_stop(fdr, fdw):
    transcode_clean(fdr, fdw)


# Get info back to encoders_comparison_tool. Function must call callback function when the status changes.
def transcode_get_info(jobid, process, fdr):
    print("transcodeGetInfo {} started.".format(jobid))
    fdr_open = os.fdopen(fdr)
    for line in fdr_open:
        stat = re.sub(r"[\n\t\s]*", "", line).rsplit("=")
        if stat[0] == "frame":
            calc = ["progress_perc", ""]
            calc[1] = format((int(stat[1])/frame_num)*100, '.2f')
            enc.transcode_callback(jobid, calc)
        if line == "progress=end\n":
            calc[1] = "100.00"
            enc.transcode_callback(jobid, calc)
        enc.transcode_callback(jobid, stat)
        if line == "progress=end\n":
            break
