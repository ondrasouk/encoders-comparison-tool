import numpy as np
import subprocess
import importlib
import threading
import concurrent.futures
import time

###########################################################
# Refactored Classes and functions that is believed usable.
###########################################################

# Everything for setting the parameters of video transcode


class Transcode_setting(object):
    """ Make an callable Transcode_setting object that returns numpy array with arguments.
    transcode_plugin    - String with the path or name of transcoder plugin.
    binary              - String with binray path or name to be executed.
    options             - Numpy array with arguments for transcoder and 
    concurrent          - Set how much paralel transcoding jobs to do. TODO
        values: -1 - number of processors
                0  - only one job
                n  - number of concurrent jobs
    """

    def __init__(self, transcode_plugin, binary, options, concurrent=0):
        self.transcode_plugin = transcode_plugin
        self.binary = binary
        self.options = options
        self.concurrent = concurrent

    def __call__(self):
        args = np.array([])
        for x in self.options:
            for y in x:
                if type(y) is str:      # self.options[x][y] is only string
                    if args.ndim != 2:  # the args is 1D array
                        args = np.append(args, y)
                    else:               # else is 2D array
                        args = np.c_[args, np.tile(y, (args.shape[0], 1))]
                elif isinstance(y, sweep_param):
                    if args.ndim == 2:  # if there is more than one sweep parameter
                        # repeat every row by number of elements on actual sweep parameter
                        args = np.repeat(args, np.size(y()), axis=0)
                        # add vector (repeated by number of actual size of args matrix
                        args = np.c_[args, np.tile(y(), (1, int(args.shape[0]/np.size(y())))).transpose()]
                    elif args.ndim == 1:
                        args = np.tile(args, (np.size(y()), 1))
                        args = np.c_[args, y().transpose()]
                    else:
                        raise Exception("Impossible error in args.ndim.")
                else:
                    raise ValueError("Options can only be strings or sweep parameters.")
        return args


class sweep_param(object):
    """ Make an callable sweep_param object that returns numpy array with sweep values.
    mode  - string
            values: 'add', 'lin', 'log' or 'list'.
    start - number, when mode is set to 'list' the input is list.
    stop  - number, when mode is set to 'list' it is not needed.
    n     - number, when mode is set to 'list' is is not needed.
    modes:
    'add' - Creates array with ascending numbers created by adding number n to previous number. Stops when next number is larger than number stop.
    'lin' - Lineary distribute n numbers between start and stop.
    'log' - Logaritmically distribute n numbers between start and stop.
    'list'- Only makes numpy array from python list.
    """

    def __init__(self, mode, start, stop=None, n=None):
        self.mode = mode
        self.start = start
        self.stop = stop
        self.n = n
        if (mode != "list") & ((stop is None) | (n is None)):
            raise ValueError("Only for mode 'list' the stop and n can be empty.")

    def __call__(self):
        return sweep(self.mode, self.start, self.stop, self.n)


def sweep(mode, start, stop, n):
    """ Make a numpy array with generated sweep.
    mode  - string
            values: 'add', 'lin', 'log' or 'list'.
    start - number, when mode is set to 'list' the input is list.
    stop  - number, when mode is set to 'list' it is not needed.
    n     - number, when mode is set to 'list' is is not needed.
    modes:
    'add' - Creates array with ascending numbers created by adding number n to previous number. Stops when next number is larger than number stop.
    'lin' - Lineary distribute n numbers between start and stop.
    'log' - Logaritmically distribute n numbers between start and stop.
    'list'- Only makes numpy array from python list.
    """
    if mode == "add":
        if (((stop - start) / n) % 1) == 0:
            values = np.arange(start, (stop + n), n)
        else:
            values = np.arange(start, stop, n)
    elif mode == "lin":
        values = np.linspace(start, stop, n)
    elif mode == "log":
        values = np.geomspace(start, stop, n)
    elif mode == "list":
        values = np.array(start)
    else:
        raise ValueError("The sweep mode can only be 'add', 'lin', 'log' or 'list'.")
    return values


# Functions for getting the video info.


def video_length_seconds(binaries, filename):
    if type(binaries) == str:
        ffprobepath = binaries
    elif type(binaries) == dict:
        ffprobepath = binaries["ffprobe"]
    else:
        raise TypeError("Passed binary can only be in format string or dictionary")

    result = subprocess.run(
        [
            ffprobepath,
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            filename,
        ],
        capture_output=True,
        text=True,
    )
    try:
        return float(result.stdout)
    except ValueError:
        raise ValueError(result.stderr.rstrip("\n"))


def video_framerate(binaries, filename):
    if type(binaries) == str:
        ffprobepath = binaries
    elif type(binaries) == dict:
        ffprobepath = binaries["ffprobe"]
    else:
        raise TypeError("Passed binary can only be in format string or dictionary")

    result = subprocess.run(
        [
            ffprobepath,
            "-v",
            "error",
            "-show_entries",
            "stream=r_frame_rate",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            filename,
        ],
        capture_output=True,
        text=True,
    )
    try:
        framerate_str = str(result.stdout.split("\n")[0])
        framerate = int(framerate_str.split("/")[0]) / int(framerate_str.split("/")[1])
        return framerate
    except ValueError:
        raise ValueError(result.stderr.rstrip("\n"))


def video_frames(binaries, filename):
    return int(video_framerate(binaries, filename) * video_length_seconds(binaries, filename))

###########################################################
# Code under heavy development.
###########################################################


class File_parameter(object):
    def __init__(self):
        pass


def transcode(binaries, videofiles, transcode_set, outputfiles):
    """ Transcode video samples in videofiles with transcode_set.
    TODO
    """
    if isinstance(transcode_set, Transcode_setting):
        print("dynamically loading source file:", transcode_set.transcode_plugin)
        spec = importlib.util.spec_from_file_location("mod", transcode_set.transcode_plugin)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        print("loaded succesfully")
        print("duration:", video_length_seconds(binaries, videofiles))
        print("framerate:", video_framerate(binaries, videofiles))
        print("calculated framecount:", video_frames(binaries, videofiles))
        process, fdr, fdw = mod.transcode_start(transcode_set.binary, videofiles, list(transcode_set()[0]), outputfiles, "ffprobe") #TODO iterate through transcode_set
        transcodeWatchdog = threading.Thread(target=transcode_watchdog, args=(process, fdr, fdw, mod))
        process.wait()
    else:
        raise ValueError("Only Transcode_setting object is passable.")


class Transcode_status(object):
    def __init__(self, is_running, progress, frames_encoded, fps, speed, out_time, line):
        self.is_running = is_running
        self.progress = progress
        self.frames_encoded = frames_encoded
        self.fps = fps
        self.speed = speed
        self.out_time = out_time
        self.line = line


def transcode_watchdog(process, fdr, fdw, mod):
    print("Monitor Thread starting.")
    transcodeGetInfo = threading.Thread(target=mod.transcode_get_info, args=(process, fdr))
    transcodeGetInfo.start()
    process.wait()
    time.sleep(0.1)
    if transcodeGetInfo.isAlive():
        try:
            print("Unclean transcode_get_info function. Cleaning.")
            mod.transcode_get_info_stop(fdw, fdr)
        except AttributeError:
            print("Not implemented external stop.\nWaiting for thread to timeout.")
        finally:
            transcodeGetInfo.join(timeout=2)
            mod.transcode_clean(fdw, fdr)
