import subprocess
import os
import re
import encoders_comparison_tool as enc
import threading
import time


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


frame_num = 1
mutex1 = threading.Lock()
mutex2 = threading.Lock()


# Internal function
def transcode_cmd(binpath, filename, args, outputfile, progress_p_w=4):
    cmd = [binpath, "-i", filename, "-nostdin", "-progress", str("pipe:" + str(progress_p_w))] + list(args) + [outputfile]
    return cmd


# Start transcode
def transcode_start(binpath, filename, args, outputfile, ffprobepath):
    mutex1.acquire()
    fdr, fdw = os.pipe()
    mutex1.release()
    cmd = transcode_cmd(binpath, filename, args, outputfile, fdw)
    global frame_num
    frame_num = enc.video_frames(ffprobepath, filename)
    process = subprocess.Popen(
        cmd,
        pass_fds=[fdw],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    # Call back into encoders_comparison_tool because the freezed libraries
    # (loaded with importlib) can't make a new thread or process.
    # Use of synchronization primitives is possible.
    return process, fdr, fdw


# Clean after transcode ended.
def transcode_clean(fdr, fdw, hard=0):
    mutex1.acquire()
    try:
        print(f"{bcolors.OKBLUE}closing fdw {fdw}{bcolors.ENDC}")
        os.close(fdw)
        print(f"{bcolors.OKGREEN}closed fdw {fdw}{bcolors.ENDC}")
    except OSError:
        print(f"{bcolors.WARNING}already closed fdw {fdw}{bcolors.ENDC}")
        pass
    if hard == 1:
        time.sleep(0.5)
        try:
            print(f"{bcolors.OKBLUE}closing fdr {fdr}{bcolors.ENDC}")
            os.close(fdr)
            print(f"{bcolors.OKGREEN}closed fdr {fdr}{bcolors.ENDC}")
    # OSError means the file descriptor is either locked, blocked or not existing (closed)
    # TODO Maybe test with fstat if the FD is closed or blocked and if blocked raise error
    # https://stackoverflow.com/questions/6916033/check-if-file-descriptor-is-valid
    #
    # Problem solved by not closing the fdr file descriptor proactively,
    # because the fdr is closed by context manager:
    # for line in fdr_open:
    # After it recieve EOF (pipe closed from fdw).
    #
        except OSError:
            print(f"{bcolors.WARNING}already closed fdr {fdr}{bcolors.ENDC}")
            pass
    mutex1.release()


# Optional: If the transcode_get_info has the risk of stuck implement this function.
def transcode_get_info_stop(fdr, fdw):
    transcode_clean(fdr, fdw, hard=1)


# Get info back to encoders_comparison_tool. Function must call callback function when the status changes.
def transcode_get_info(jobid, process, fdr):
    print("transcodeGetInfo {} started.".format(jobid))
    fdr_open = os.fdopen(fdr, "r")
    print(f"{bcolors.OKBLUE}{jobid} Pipe {fdr} openned for reading{bcolors.ENDC}")
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
