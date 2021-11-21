import subprocess
import os
import re
import encoders_comparison_tool as enc


# Colors in terminal

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


frame_num = {}


# Internal function
def transcode_cmd(binpath, filename, args, outputfile, progress_p_w=4):
    cmd = [binpath, "-i", filename, "-nostdin", "-progress", str("pipe:" + str(progress_p_w))] + list(args) + [outputfile]
    print(" ".join(cmd))
    return cmd


# Start transcode
def transcode_start(binpath, filename, args, outputfile, ffprobepath):
    frame_num[filename] = enc.video_frames(ffprobepath, filename)
    fdr, fdw = os.pipe()
    if os.name == "posix":
        cmd = transcode_cmd(binpath, filename, args, outputfile, fdw)
        process = subprocess.Popen(
            cmd,
            pass_fds=[fdw],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
    elif os.name == "nt":
        fdw_dup = 0
        fdw_dup = os.dup2(fdw, fdw_dup, inheritable=True)
        os.close(fdw)
        #
        # Workaround: Use custom made pipe at stdin.
        # Subprocess module is as close to native implementation as possible
        # so under Windows the handles with inheritance are passed, but
        # PIPE is file descriptor and there is almost no way around it.
        # Python creates file descriptors for pipes at execution, only possible
        # fix is writing my implementation that will wire up handle of PIPE to
        # PIPE of the process.
        # Probably in future there will be a fix for this.
        # Associated BUG tracker and PR:
        # https://bugs.python.org/issue32865
        # https://github.com/python/cpython/pull/13739
        #
        cmd = transcode_cmd(binpath, filename, args, outputfile, fdw_dup)
        process = subprocess.Popen(
            cmd,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            close_fds=True,
        )
    else:
        raise Exception("Use Windows or Posix, other platforms not tested not tested.")
    # Return into encoders_comparison_tool because the freezed libraries
    # (loaded with importlib) can't make a new thread or process.
    return process, fdr, fdw


# Clean after transcode ended.
def transcode_clean(fdw):
    try:
        os.close(fdw)
    except OSError:
        print(f"{bcolors.WARNING}already closed fdr {fdr}{bcolors.ENDC}")
        pass
    #
    # Problem solved by not closing the fdr file descriptor,
    # because the fdr is closed by context manager:
    # for line in fdr_open:
    # After it recieve EOF (pipe closed from fdw).
    #


# Optional: If the transcode_get_info has the risk of stuck, implement this function.
def transcode_get_info_stop(fdr, fdw):
    transcode_clean(fdw)


# Get info back to encoders_comparison_tool. Function must call callback function when the status changes.
def transcode_get_info(jobid, process, fdr):
    print("transcodeGetInfo {} started.".format(jobid))
    fdr_open = os.fdopen(fdr)
    for line in fdr_open:
        stat = re.sub(r"[\n\t\s]*", "", line).rsplit("=")
        if stat[0] == "frame":
            calc = ["progress_perc", ""]
            calc[1] = format((int(stat[1])/frame_num[process.args[2]])*100, '.2f')
            enc.transcode_callback(jobid, calc)
        if line == "progress=end\n":
            calc[1] = "100.00"
            enc.transcode_callback(jobid, calc)
        enc.transcode_callback(jobid, stat)
        if line == "progress=end\n":
            break

# Make a function for testing configuration without actually running actual
# transcode. For this it can be used Null demux and muxer and encode of 1 frame
# to test the functionality of libraries that don't have test before the codecs
# fails and throws error.
# https://trac.ffmpeg.org/wiki/Null
