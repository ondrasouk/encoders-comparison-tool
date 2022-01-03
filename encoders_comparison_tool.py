import os
import time
import subprocess
import threading
import concurrent.futures as cf
from importlib import util
import numpy as np


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


# Everything for setting the parameters of video transcode

# Videofiles properties. Key is video file path.
videofiles_frame_num = {}
videofiles_duration = {}
videofiles_framerate = {}

# Index corresponds to job_id.
status = np.array([{}])


class Transcode_setting(object):
    """ Make an callable Transcode_setting object that returns numpy array with arguments.

    transcode_plugin    - String with the path or name of transcoder plugin.
    binary              - String with binray path or name to be executed.
    options             - Numpy array or matrix with arguments for transcoder
    concurrent          - Set how much paralel transcoding jobs to do.
        values: -1 - number of processors
                n > 0  - number of concurrent jobs for this setting

    class functions:
    options_flat() - Make an numpy array (1D) with arguments and settings.
    param_find() - Find an sweep_param in options and return where is it in
        options_flat() and what is proceeding it
    """

    def __init__(self, transcode_plugin: str, binary: str, options, concurrent: int = 0):
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
                    if args.ndim == 2:  # if there is more than one sweep
                        # parameter repeat every row by number of elements on
                        # actual sweep parameter
                        args = np.repeat(args, np.size(y()), axis=0)
                        # add vector (repeated by number of actual size of args matrix)
                        args = np.c_[args, np.tile(y(), (1, int(args.shape[0]/np.size(y())))).transpose()]
                    elif args.ndim == 1:  # if this is first sweep
                        args = np.tile(args, (np.size(y()), 1))
                        args = np.c_[args, y().transpose()]
                    else:
                        raise Exception("Impossible error in args.ndim.")
                else:
                    raise ValueError("Options can only be strings or sweep parameters.")
        return args

    def options_flat(self):
        """ Make an numpy array (1D) with arguments and settings.
        Use on Transcode_setting object.
        Returns: ['-c:v', 'libx265', '-crf', <sweep_param object>, '-an']
        """
        flat = []
        for x in self.options:
            for y in x:
                flat.append(y)
        return flat

    def param_find(self):
        """ Find an sweep_param in options of Transcode_setting object.
        Use on Transcode_setting object.
        Returns touple (param_name, param_value)
        param_name - List of names before sweep_param objects.
        param_value - position where to find the parametric values.
            eg. options = ["-b:v", enc.sweep_param("add", 1, 10, 1, "", "M")]
            returns (["-b:v"], [1])
        """
        flat = self.options_flat()
        param_name = []
        param_value = []
        for x in range(len(flat)):
            if isinstance(flat[x], sweep_param):
                if x == 0:
                    param_name.append("")
                else:
                    param_name.append(flat[x-1])
                param_value.append(x)
        return param_name, param_value

    def edge_cases(self):
        args = np.array([])
        for x in self.options:
            for y in x:
                if type(y) is str:      # self.options[x][y] is only string
                    if args.ndim != 2:  # the args is 1D array
                        args = np.append(args, y)
                    else:               # else is 2D array
                        args = np.c_[args, np.tile(y, (args.shape[0], 1))]
                elif isinstance(y, sweep_param):
                    if args.ndim == 2:  # if there is more than one sweep
                        # parameter repeat every row by number of elements on
                        # actual sweep parameter
                        args = np.repeat(args, np.size(y.limits()), axis=0)
                        # add vector (repeated by number of actual size of args matrix)
                        args = np.c_[args, np.tile(y.limits(), (1, int(args.shape[0]/np.size(y.limits())))).transpose()]
                    elif args.ndim == 1:  # if this is first sweep
                        args = np.tile(args, (np.size(y.limits()), 1))
                        args = np.c_[args, y.limits().transpose()]
                    else:
                        raise Exception("Impossible error in args.ndim.")
                else:
                    raise ValueError("Options can only be strings or sweep parameters.")
        return args

    def is_pos_param(self, pos: int) -> bool:
        param_name, param_value = self.param_find()
        if pos not in param_value:
            raise ValueError(f"param_pos={pos} is not pointing to sweep_param object. sweep_param is at {param_value}")
        return True


class args_iterator(object):
    """ Make an iterator of videofiles and transcode_set
    videofiles - iterable object with inputfile names
    transcode_set - transcode_set()
    """

    def __init__(self, videofiles, transcode_set):
        self.videofiles = videofiles
        self.transcode_set = transcode_set

    def __iter__(self):
        for inputfile in self.videofiles:
            if self.transcode_set.ndim == 1:
                yield inputfile, list(self.transcode_set)
            else:
                for transcode_args in self.transcode_set:
                    yield inputfile, list(transcode_args)


class sweep_param(object):
    """ Make an callable sweep_param object that returns numpy array with sweep values.
    mode  - string
            values: 'add', 'lin', 'log' or 'list'.
    start - number, when mode is set to 'list' the input is list.
    stop  - number, when mode is set to 'list' it is not needed.
    n     - number, when mode is set to 'list' is is not needed.
    prefix - string, optional. Not used in 'list' mode.
    suffix - string, optional. Not used in 'list' mode.
    modes:
    'add' - Creates array with ascending numbers created by adding number n to previous number. Stops when next number is larger than number stop.
    'lin' - Lineary distribute n numbers between start and stop.
    'log' - Logaritmically distribute n numbers between start and stop.
    'list'- Only makes numpy array from python list.
    """

    def __init__(self, mode, start, stop=None, n=None, prefix="", suffix=""):
        self.mode = mode
        self.start = start
        self.stop = stop
        self.n = n
        self.prefix = str(prefix)
        self.suffix = str(suffix)
        if (mode != "list") & ((stop is None) | (n is None)):
            raise ValueError("Only for mode 'list' the stop and n can be empty.")

    def __call__(self):
        return sweep(self.mode, self.start, self.stop, self.n, self.prefix, self.suffix)

    def limits(self):
        if self.mode == "list":
            return self()
        else:
            return self()[0], self()[-1]


def sweep(mode, start, stop, n, prefix, suffix):
    """ Make a numpy array with generated sweep.
    mode   - string
             values: 'add', 'lin', 'log' or 'list'.
    start  - number, when mode is set to 'list' the input is list.
    stop   - number, when mode is set to 'list' it is not needed.
    n      - number, when mode is set to 'list' is is not needed.
    prefix - string, when mode is set to 'list' is is not needed.
    suffix - string, when mode is set to 'list' is is not needed.
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
        return values
    else:
        raise ValueError("The sweep mode can only be 'add', 'lin', 'log' or 'list'.")
    if values.dtype == "int64":
        values = np.char.mod('%d', values)
    else:
        values = np.char.mod('%.3f', values)
    values = np.char.add(prefix, values)
    values = np.char.add(values, suffix)
    return values


def count(n=0):
    while True:
        yield n
        n += 1


def transcode_args(binaries, mod, transcode_set, videofiles, output_path):
    param_name, param_value = transcode_set.param_find()
    args_in = []
    jobid = count()
    transcode_args_iter = args_iterator(videofiles, transcode_set())
    for inputfile, transcode_args in transcode_args_iter:
        filebasename = os.path.splitext(os.path.basename(inputfile))[0]
        outputfile = str(output_path + filebasename + ".mkv")
        param = ""
        x = count()
        if param_name == []:
            args_in.append((next(jobid), mod, transcode_set.binary, inputfile, transcode_args, outputfile, binaries["ffprobe"]))
        else:
            for opt in param_name:
                param = param + opt + "_" + str(transcode_args[param_value[next(x)]])
            outputfile = str(filebasename + param)
            for ch in ['\\', '/', '|', '*', '"', '?', ':', '<', '>']:
                if ch in outputfile:
                    outputfile = outputfile.replace(ch, "")
            outputfile = str(output_path + outputfile + ".mkv")
            print(outputfile)
            args_in.append((next(jobid), mod, transcode_set.binary, inputfile, list(transcode_args), outputfile, binaries["ffprobe"]))
    return args_in

# Functions for getting the video info.


def video_length_seconds(binaries, videofile_path):
    if type(binaries) == str:
        ffprobepath = binaries
    elif type(binaries) == dict:
        ffprobepath = binaries["ffprobe"]
    else:
        raise TypeError("Passed binary can only be in format string or dictionary")

    global videofiles_duration
    try:
        duration = videofiles_duration[videofile_path]
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
                videofile_path,
            ],
            capture_output=True,
            text=True,
        )
        try:
            return float(result.stdout)
        except ValueError:
            raise ValueError(result.stderr.rstrip("\n"))


def video_framerate(binaries, videofile_path):
    if type(binaries) == str:
        ffprobepath = binaries
    elif type(binaries) == dict:
        ffprobepath = binaries["ffprobe"]
    else:
        raise TypeError("Passed binary can only be in format string or dictionary")

    global videofiles_duration
    try:
        framerate = videofiles_framerate[videofile_path]
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
                videofile_path,
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


def video_frames(binaries, videofile_path):
    return int(video_framerate(binaries, videofile_path) * video_length_seconds(binaries, videofile_path))

###########################################################
# Code for transcoding
###########################################################


def transcode(binaries, videofiles, transcode_set, output_path):
    print(f"Dynamically loading source file: {transcode_set.transcode_plugin}")
    spec = util.spec_from_file_location("mod", transcode_set.transcode_plugin)
    mod = util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    print("Module loaded succesfully!")
    for video in videofiles:
        print(f"{video} duration: {video_length_seconds(binaries, video)}")
        print(f"{video} framerate: {video_framerate(binaries, video)}")
        print(f"{video} calculated framecount: {video_frames(binaries, video)}")

    args_in = transcode_args(binaries, mod, transcode_set, videofiles, output_path)
    print(args_in)

    global status
    not_started_job_status = {'frame': '0', 'fps': '0.00', 'total_size': '0', 'out_time': '00:00:00.000000', 'speed': '0.00x', 'progress': 'waiting', 'progress_perc': '0.00'}
    for i in range(len(args_in)-1):  # job_id starts from 0
        status = np.append(status, not_started_job_status.copy())

    if transcode_set.concurrent == 0:
        concurrency = 1
    elif transcode_set.concurrent == -1:
        concurrency = len(os.sched_getaffinity(0))
    else:
        concurrency = transcode_set.concurrent
        # TODO Do not use more than 61 threads under Windows
        # https://stackoverflow.com/questions/1006289/how-to-find-out-the-number-of-cpus-using-python

    with cf.ThreadPoolExecutor(max_workers=concurrency, thread_name_prefix='job') as pool:
        futures = tuple(pool.submit(transcode_job_wrap, *args) for args in tuple(args_in))

    for future in futures:
        print(f"Exceptions on job {future.result()[0]}: {future.exception()}")


def transcode_job_wrap(jobid, mod, binary, inputfile, transcode_opt, outputfile, ffprobepath):
    process, fdr, fdw = mod.transcode_start(binary, inputfile, transcode_opt, outputfile, ffprobepath)
    print("job started.")
    transcodeGetInfo = threading.Thread(target=mod.transcode_get_info, args=(jobid, process, fdr))
    transcodeGetInfo.start()
    print("Monitor Thread starting.")
    while process.poll() is None:
        line = process.stdout.readline().rstrip("\n")
        # Read from stdout, because Windows has blocking pipes.
        # TODO For GUI usage there must be callback
    process.wait()
    if transcodeGetInfo.is_alive():
        time.sleep(0.1)
        if transcodeGetInfo.is_alive():
            try:
                print(f"{bcolors.FAIL}Hanged transcode_get_info on {jobid}. Cleaning.{bcolors.ENDC}")
                mod.transcode_get_info_stop(fdr, fdw)
            except AttributeError:
                print(f"{bcolors.WARNING}Not implemented external stop.\nWaiting for thread to timeout.{bcolors.ENDC}")
            finally:
                transcodeGetInfo.join(timeout=2)
    else:
        mod.transcode_clean(fdw)
    if (process.returncode > 0):
        raise ValueError("command: {}\n failed with returncode: {}\nProgram output:\n{}".format(" ".join(process.args), process.returncode, process.stdout.read()))
    return jobid, process.returncode


def transcode_callback(jobid, stat):
    status[jobid][stat[0]] = stat[1]
    if stat[0] == "progress":
        try:
            for i in range(len(status)):
                print(f"job id {i} progress: {status[i]['progress_perc']}%")
        except KeyError:
            pass


def transcode_check(binaries, videofiles, transcode_set, mode="quick", param_pos=None):
    print(f"Dynamically loading source file: {transcode_set.transcode_plugin}")
    spec = util.spec_from_file_location("mod", transcode_set.transcode_plugin)
    mod = util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    print("Module loaded succesfully!")
    args = []
    if transcode_set().ndim == 1:
        args = transcode_set()
    elif param_pos is None and mode == "quick":
        args = transcode_set.edge_cases()
    elif param_pos is None and mode == "slow":
        args = transcode_set()
    elif mode == "quick":
        transcode_set.is_pos_param(param_pos)
        param_name, param_value = transcode_set.param_find()
        lim = transcode_set.options_flat()[param_pos].limits()
        arg = transcode_set.options_flat()
        for p in param_value:
            arg[p] = arg[p]()[0]
        for x in lim:
            arg[param_pos] = x
            args.append(arg.copy())
    elif mode == "slow":
        transcode_set.is_pos_param(param_pos)
        param_name, param_value = transcode_set.param_find()
        param = transcode_set.options_flat()[param_pos]()
        arg = transcode_set.options_flat()
        for p in param_value:
            arg[p] = arg[p]()[0]
        for x in param:
            arg[param_pos] = x
            args.append(arg.copy())
    else:
        raise ValueError("Wrong input mode.")
    print(f"check args: {args}")
    returncodes = []
    if mode == "quick":
        for arg in args:
            returncodes.append(mod.transcode_check_arguments(transcode_set.binary, "", arg, binaries, mode))
    else:
        for inputfile in videofiles:
            for arg in args:
                returncodes.append(mod.transcode_check_arguments(transcode_set.binary, inputfile, arg, binaries, mode))
    return all(v == 0 for v in returncodes)
