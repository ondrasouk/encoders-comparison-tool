import numpy as np
import time
import subprocess
import importlib
import threading
import multiprocessing
import concurrent.futures as cf
import os


###########################################################
# Refactored Classes and functions that is maybe finalized.
###########################################################

# Everything for setting the parameters of video transcode

# Videofiles properties. Key is filename.
videofiles_frame_num = {}
videofiles_duration = {}
videofiles_framerate = {}


class Transcode_setting(object):
    """ Make an callable Transcode_setting object that returns numpy array with arguments.
    transcode_plugin    - String with the path or name of transcoder plugin.
    binary              - String with binray path or name to be executed.
    options             - Numpy array with arguments for transcoder
    concurrent          - Set how much paralel transcoding jobs to do. TODO
        values: -1 - number of processors
                n > 0  - number of concurrent jobs for this setting
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

    global videofiles_duration
    try:
        duration = videofiles_duration[filename]
        return duration
    except KeyError:
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

    global videofiles_duration
    try:
        framerate = videofiles_framerate[filename]
        return framerate
    except KeyError:
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


def transcode(binaries, videofiles, transcode_set, outputpath):
    """ Transcode video samples in videofiles with transcode_set.
    TODO
    """
    if isinstance(transcode_set, Transcode_setting):
        print("Dynamically loading source file:", transcode_set.transcode_plugin)
        spec = importlib.util.spec_from_file_location("mod", transcode_set.transcode_plugin)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        print("Module loaded succesfully!")
        for inputfile in videofiles:
            print(inputfile, "duration:", video_length_seconds(binaries, inputfile))
            print(inputfile, "framerate:", video_framerate(binaries, inputfile))
            print(inputfile, "calculated framecount:", video_frames(binaries, inputfile))

        options_flat = []
        for x in transcode_set.options:
            for y in x:
                options_flat.append(y)

        param_name = []
        param_value = []
        for x in range(len(options_flat)):
            if isinstance(options_flat[x], sweep_param):
                if x == 0:
                    param_name.append("")
                else:
                    param_name.append(options_flat[x-1])
                param_value.append(x)

        args_in = []
        jobid = iter([x for x in range(99999)])
        for inputfile in videofiles:
            filebasename = os.path.splitext(os.path.basename(inputfile))[0]
            for transcode_args in transcode_set():
                x = iter([x for x in range(99999)])
                param = ""
                for opt in param_name:
                    param = param + opt + "-" + str(transcode_args[param_value[next(x)]])
                outputfile = str(outputpath + filebasename + param + ".mkv")
                print(outputfile)
                args_in.append((next(jobid), mod, transcode_set.binary, inputfile, list(transcode_args), outputfile, binaries["ffprobe"]))
        print(args_in)
        global status
        if 'status' not in globals():
            status = np.array([{}])
        not_started_job_status = {'frame': '298', 'fps': '0.00', 'total_size': '0', 'out_time': '00:00:00.000000', 'speed': '0.00x', 'progress': 'waiting', 'progress_perc': '0.00'}
        for i in range(next(jobid)-1):
            status = np.append(status, not_started_job_status.copy())
        if transcode_set.concurrent == 0:
            concurrency = 1
        elif transcode_set.concurrent == -1:
            concurrency = multiprocessing.cpu_count()  # TODO maybe use len(os.sched_getaffinity(0))
        else:
            concurrency = transcode_set.concurrent
            # TODO Do not use more than 61 threads under Windows (needs test for this)
            # https://stackoverflow.com/questions/1006289/how-to-find-out-the-number-of-cpus-using-python
        print(concurrency)

        with cf.ThreadPoolExecutor(max_workers=concurrency, thread_name_prefix='job') as pool:
            futures = tuple(pool.submit(transcode_job_wrap, *args) for args in tuple(args_in))

        jobid = iter([x for x in range(99999)])
        for future in futures:
            print("Exceptions on job:", next(jobid), ":", future.exception())
    else:
        raise TypeError("Only Transcode_setting class object is passable.")


def transcode_job_wrap(jobid, mod, binary, inputfile, transcode_opt, outputfile, ffprobepath):
    print("job started.")
    process, fdr, fdw = mod.transcode_start(binary, inputfile, transcode_opt, outputfile, ffprobepath)
    print("Monitor Thread starting.")
    transcodeGetInfo = threading.Thread(target=mod.transcode_get_info, args=(jobid, process, fdr))
    transcodeGetInfo.start()
    process.wait()
    print("returncode:", process.returncode)
    time.sleep(0.1)
    if transcodeGetInfo.isAlive():
        try:
            print("Unclean transcode_get_info function. Cleaning.")
            mod.transcode_get_info_stop(fdr, fdw)
        except AttributeError:
            print("Not implemented external stop.\nWaiting for thread to timeout.")
        finally:
            transcodeGetInfo.join(timeout=2)
    else:
        print("transcodeGetInfo exited normally.")
        mod.transcode_clean(fdr, fdw)
    if (process.returncode > 0):
        raise ValueError("command: {}\n failed with returncode: {}\nProgram output:\n{}".format(" ".join(process.args), process.returncode, process.stderr.read()))
    return process.returncode


def transcode_callback(jobid, stat):
    status[jobid][stat[0]] = stat[1]
    if stat[0] == "progress":
        try:
            for i in range(len(status)):
                print("job id", i, ":", "progress:", status[i]["progress_perc"], "%")
        except KeyError:
            pass
