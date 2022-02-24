import os
import time
import subprocess
import threading
import concurrent.futures as cf
from importlib import util
import numpy as np
import psutil


MONITOR_PROC_SECS = 0.1


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

binaries = {}
# Videofiles properties. Key is video file path.
videofiles_frame_num = {}
videofiles_duration = {}
videofiles_framerate = {}
videofiles_resolution = {}
videofiles_pix_fmt = {}
pix_fmts_bpp = {}

# Index corresponds to job_id.
#status = np.array([{}])
job_list = []


class Transcode_setting(object):
    """ Make an callable object that returns numpy array with arguments.

    Attributes:
        transcode_plugin: String with the path or name of transcode plugin.
        binary:  String with binray path or name to be executed.
        options: Numpy array or matrix with arguments for encoder.
        concurrent: Set how much paralel transcoding jobs to do.
            values: -1 - number of processors
                    n > 0  - number of concurrent jobs for this setting

    class functions:
        self(): Make an 2D Numpy array with arguments for transcode.
        options_flat(): Make an numpy array (1D) with arguments and settings.
        param_find(): Find an sweep_param in options and return where is it in
            options_flat() and what is proceeding it.
        edge_cases(): Like self(), but skips in num. sweep middle values.
        is_pos_param(pos): If at pos is no sweep_param raises ValueError.
    """

    def __init__(self,
                 transcode_plugin: str,
                 binary: str,
                 options,
                 concurrent: int = 0,
                 two_pass: bool = False):
        self.transcode_plugin = transcode_plugin
        self.binary = binary
        self.options = options
        self.concurrent = concurrent
        self.two_pass = two_pass

    def __call__(self):
        """ Make an 2D Numpy array with arguments for transcode.

        Returns: Combination of every sweep_param values.
        """
        args = np.array([])
        for x in self.options:
            for y in x:
                if type(y) is str:  # self.options[x][y] is only string
                    if args.ndim != 2:  # the args is 1D array
                        args = np.append(args, y)
                    else:  # else is 2D array
                        args = np.c_[args, np.tile(y, (args.shape[0], 1))]
                elif isinstance(y, sweep_param):
                    if args.ndim == 2:  # if there is more than one sweep
                        # parameter repeat every row by number of elements on
                        # actual sweep parameter
                        args = np.repeat(args, np.size(y()), axis=0)
                        # add vector (repeated by number of actual size of args
                        # matrix)
                        args = np.c_[args,
                                     np.tile(y(),
                                             (1,
                                              int(args.shape[0] /
                                                  np.size(y())))).transpose()]
                    elif args.ndim == 1:  # if this is first sweep
                        args = np.tile(args, (np.size(y()), 1))
                        args = np.c_[args, y().transpose()]
                    else:
                        raise Exception("Impossible error in args.ndim.")
                else:
                    raise ValueError(
                        "Options can only be strings or sweep parameters.")
        return args

    def options_flat(self):
        """ Make an numpy array (1D) with arguments and settings.

        Returns: 1D array of self.options.
            example: ['-c:v', 'libx265', '-crf', <sweep_param object>, '-an']
        """
        flat = []
        for x in self.options:
            for y in x:
                flat.append(y)
        return flat

    def param_find(self):
        """ Find an sweep_param in options of Transcode_setting object.

        Returns: touple (param_name, param_pos)
            param_name: List of names before sweep_param objects.
            param_pos: position where to find the parametric values.
                eg. options = ["-crf", enc.sweep_param("add", 15, 27, 1)]
                    returns (["-crf"], [1])
        """
        flat = self.options_flat()
        param_name = []
        param_pos = []
        for x in range(len(flat)):
            if isinstance(flat[x], sweep_param):
                if x == 0:
                    param_name.append("")
                else:
                    param_name.append(flat[x - 1])
                param_pos.append(x)
        return param_name, param_pos

    def edge_cases(self):
        """ Like self(), but skips in num. sweep middle values.

        Returns: Combination of sweep_param edge values.
        """
        args = np.array([])
        for x in self.options:
            for y in x:
                if type(y) is str:  # self.options[x][y] is only string
                    if args.ndim != 2:  # the args is 1D array
                        args = np.append(args, y)
                    else:  # else is 2D array
                        args = np.c_[args, np.tile(y, (args.shape[0], 1))]
                elif isinstance(y, sweep_param):
                    if args.ndim == 2:  # if there is more than one sweep
                        # parameter repeat every row by number of elements on
                        # actual sweep parameter
                        args = np.repeat(args, np.size(y.edge()), axis=0)
                        # add vector (repeated by number of actual size of args
                        # matrix)
                        args = np.c_[args,
                                     np.tile(y.edge(), (
                                         1,
                                         int(args.shape[0] /
                                             np.size(y.edge())))).transpose()]
                    elif args.ndim == 1:  # if this is first sweep
                        args = np.tile(args, (np.size(y.edge()), 1))
                        args = np.c_[args, y.edge().transpose()]
                    else:
                        raise Exception("Impossible error in args.ndim.")
                else:
                    raise ValueError(
                        "Options can only be strings or sweep parameters.")
        return args

    def is_pos_param(self, pos: int) -> bool:
        """ Tests if sweep_param is at pos, if not raises ValueError. """
        param_name, param_value = self.param_find()
        if pos not in param_value:
            raise ValueError(
                f"param_pos={pos} is not pointing to sweep_param object. sweep_param is at {param_value}"
            )
        return True


class sweep_param(object):
    """ Make callable sweep_param object, returns np.array with sweep values.

    Attributes:
        mode: Values: 'add', 'lin', 'log' or 'list'.
        start: Number, when mode is set to 'list' the input is list.
        stop: Number, when mode is set to 'list' it is not needed.
        n: Number, when mode is set to 'list' is is not needed.
        prefix: String, optional. Not used in 'list' mode.
        suffix: String, optional. Not used in 'list' mode.

    modes:
        'add': Creates array with ascending numbers created by adding number n
        to previous number. Stops when next number is larger than number stop.
        'lin': Lineary distribute n numbers between start and stop.
        'log': Logaritmically distribute n numbers between start and stop.
        'list': Only makes numpy array from python list.
    """

    def __init__(self, mode, start, stop=None, n=None, prefix="", suffix=""):
        self.mode = mode
        self.start = start
        self.stop = stop
        self.n = n
        self.prefix = str(prefix)
        self.suffix = str(suffix)
        if (mode != "list") & ((stop is None) | (n is None)):
            raise ValueError(
                "Only for mode 'list' the stop and n can be empty.")

    def __call__(self):
        return sweep(self.mode, self.start, self.stop, self.n, self.prefix,
                     self.suffix)

    def edge(self):
        """ Make reduced sweep to only edge values, if not 'list'. """
        if self.mode == "list":
            return self()
        else:
            return self()[0], self()[-1]


def sweep(mode, start, stop, n, prefix, suffix):
    """ Make a numpy array with generated sweep.

    Args:
        mode: Values: 'add', 'lin', 'log' or 'list'.
        start: number, when mode is set to 'list' the input is list.
        stop: number, when mode is set to 'list' it is not needed.
        n: number, when mode is set to 'list' is is not needed.
        prefix: string, when mode is set to 'list' is is not needed.
        suffix: string, when mode is set to 'list' is is not needed.

    modes:
        'add': Creates array with ascending numbers created by adding number n
        to previous number. Stops when next number is larger than number stop.
        'lin': Lineary distribute n numbers between start and stop.
        'log': Logaritmically distribute n numbers between start and stop.
    '   list': Only makes numpy array from python list.
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
        raise ValueError(
            "The sweep mode can only be 'add', 'lin', 'log' or 'list'.")
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


# TODO
# unused for now
class inputfile_variants(object):
    def __init__(self):
        self.variants = []
        self.inputfiles_variants = {}
        self.variants_used = {}
        self.lock = threading.Lock()

    def request_variant(self, inputfile, file_format, pix_format="", jobid=None):
        self.lock.acquire()
        filebasename = os.path.splitext(os.path.basename(inputfile))[0]
        outputfile = filebasename + "_" + pix_format + "." + file_format
        if outputfile in self.variants:
            self.variants_used["outputfile"] = self.variants_used["outputfile"] + 1
            if file_format == "yuv":
                return outputfile, video_get_info_for_yuv()
            else:
                return outputfile

        spec = util.spec_from_file_location("mod", "ffmpeg_transcode.py")
        mod = util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        if file_format == "yuv":
            pass
        self.lock.release()
        return outputfile

    def free_variant(self, variant_path):
        self.lock.acquire()
        self.lock.release()

    def clean_variants(self):
        self.lock.acquire()
        self.lock.release()


class Transcode_job:
    def __init__(self, transcode_set, job_id, mod, args, inputfile, outputfile, binaries):
        self.transcode_set = transcode_set
        self.binary = transcode_set.binary
        self.job_id = job_id
        self.mod = mod
        self.args = args
        self.inputfile = inputfile
        self.outputfile = outputfile
        if mod.OUTPUT_UNSUPORTED_BY_FFMPEG:
            self.encodedfile = os.path.splitext(outputfile)[0] + mod.ENCODED_FILE_TYPE
        else:
            self.encodedfile = outputfile
        self.two_pass = transcode_set.two_pass
        self.binaries = binaries
        self.finished = False
        self.status = {
            'frame': '0',
            'fps': '0.00',
            'total_size': '0',
            'out_time': '00:00:00.000000',
            'speed': '0.00x',
            'progress': 'waiting',
            'progress_perc': '0.00',
            'state': 'waiting'  # for indicating two-pass and other processing
        }
        self.PID = None
        self.cpu_useage = None
        self.mem_useage = None
        self.basename = os.path.splitext(outputfile)[0]
        self.useage_logfile = self.basename + "_useage.log"
        self.report = self.basename + ".report"  # verbose log or stdout record
        with open(self.useage_logfile, 'w') as logfile:
            logfile.write("time,state,cpu_time_user,cpu_time_system,cpu_time_children_user,cpu_time_children_system,cpu_time_iowait,cpu_percent,RSS,VMS\n")
        if os.path.splitext(inputfile)[1] in mod.INPUT_FILE_TYPE:
            self.inputfile_variant = None
        else:
            mod.get_input_variant(self)


###########################################################
# Code for monitoring and recording encoding resources useage
###########################################################


class PerpetualTimer:
    """
    Run code periodically in thread.
    More info: https://stackoverflow.com/a/40965385
    """

    def __init__(self, interval, function, *args, **kwargs):
        self._timer = None
        self.interval = interval
        self.function = function
        self.args = args
        self.kwargs = kwargs
        self.is_running = False
        self.next_call = time.time()
        self.start()

    def _run(self):
        self.is_running = False
        self.start()
        self.function(*self.args, **self.kwargs)

    def start(self):
        if not self.is_running:
            self.next_call += self.interval
            self._timer = threading.Timer(self.next_call - time.time(), self._run)
            self._timer.start()
            self.is_running = True

    def cancel(self):
        self._timer.cancel()
        self.is_running = False


def record_useage():
    global job_list
    for job in job_list:
        if job.PID is not None:
            proc = psutil.Process(job.PID)
            with proc.oneshot():
                p = proc.cpu_times()
                p_percent = proc.cpu_percent()
                m = proc.memory_info()
            msg = f"{p.user},{p.system},{p.children_user},{p.children_system},{p.iowait},{p_percent},{m.rss},{m.vms}"
            with open(job.useage_logfile, 'a') as logfile:
                logfile.write(f"{time.time() - proc.create_time()},{job.status['state']},{msg}\n")
            job.cpu_useage = p_percent
            job.mem_useage = m.rss


###########################################################
# Code for transcoding
###########################################################


def transcode(binaries_ent, videofiles, transcode_set, output_path):
    """ Make batch transcode.

    Args:
        binaries_ent: Dictionary with binaries and their path.
        videofiles: Iterable containing path to video files.
        transcode_set: Transcode_setting object.
        output_path: Path to folder where transcoded videos will be outputed.
    """
    global binaries
    binaries = binaries_ent.copy()
    print(f"Dynamically loading source file: {transcode_set.transcode_plugin}")
    spec = util.spec_from_file_location("mod", transcode_set.transcode_plugin)
    mod = util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    print("Module loaded succesfully!")
    for video in videofiles:
        print(f"{video} duration: {video_length_seconds(video)}")
        print(f"{video} framerate: {video_framerate(video)}")
        print(f"{video} calculated framecount: {video_frames(video)}")

    param_name, param_value = transcode_set.param_find()
    global job_list
    for videofile, args in [[videofile, args] for videofile in videofiles for args in transcode_set()]:
        filebasename = os.path.splitext(os.path.basename(videofile))[0]
        param = ""
        x = count()
        if param_name == []:
            outputfile = str(output_path + filebasename + ".mkv")
        else:
            for opt in param_name:
                param = param + opt + "_" + str(
                    args[param_value[next(x)]])
            outputfile = str(filebasename + param)
            for ch in ['\\', '/', '|', '*', '"', '?', ':', '<', '>']:
                # erase forbidden characters in file names
                if ch in outputfile:
                    outputfile = outputfile.replace(ch, "")
            outputfile = str(output_path + outputfile + ".mkv")
        job_list.append(Transcode_job(transcode_set, len(job_list), mod, args, videofile, outputfile, binaries_ent))

    if transcode_set.concurrent == 0:
        concurrency = 1
    elif transcode_set.concurrent == -1:
        concurrency = len(os.sched_getaffinity(0))
    else:
        concurrency = transcode_set.concurrent
        # TODO Do not use more than 61 threads under Windows.
        # https://stackoverflow.com/questions/1006289/how-to-find-out-the-number-of-cpus-using-python

    monitor = PerpetualTimer(MONITOR_PROC_SECS, record_useage)
    monitor.start()

    with cf.ThreadPoolExecutor(max_workers=concurrency,
                               thread_name_prefix='job') as pool:
        futures = tuple(
            pool.submit(mod.transcode_start, job) for job in job_list)

    for future in futures:
        print(f"Exceptions on job {future.result()[0]}: {future.exception()}")
    monitor.cancel()


def transcode_status_update_callback(job, stat):
    """ Callback from module to update status.

    Args:
        job: Transcode_job object
        stat: status to commit to global variable
    """
    try:
        job.status[stat[0]] = stat[1]
    except IndexError:
        print(f"IndexError: {stat}")
    if stat[0] == "progress":
        try:
            for i in range(len(job_list)):
                print(f"job id {i}, state: {job.status['state']}, progress: {job.status['progress_perc']}%")
        except KeyError:
            pass


def transcode_stdout_update_callback(job, line):
    """ Callback from module to update stdout.

    Args:
        jobid: job id
        line: last line from stdout.
    """
    pass
    # Read from stdout, because Windows has blocking pipes.
    # TODO For GUI usage there must be callback


def transcode_check(binaries_ent,
                    videofiles,
                    transcode_set,
                    mode="quick",
                    param_pos=None):
    """ Do check of config.

    Primary usage is for GUI.

    Args:
        binaries_ent: Dictionary with binaries and their path.
        videofiles: Iterable containing path to video files.
        transcode_set: Transcode_setting object.
        mode: Values: 'quick' or 'slow'
        param_pos: Position of sweep_param object in options_flat().

    modes:
        'quick': Test only edge cases and with faster settings.
        'slow': Test every combination and test input files.

    Returns: True if all checks ended with return code 0.
    """
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
        lim = transcode_set.options_flat()[param_pos].edge()
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
            returncodes.append(
                mod.transcode_check_arguments(transcode_set.binary, "", arg,
                                              binaries_ent, mode))
    else:
        for inputfile in videofiles:
            for arg in args:
                returncodes.append(
                    mod.transcode_check_arguments(transcode_set.binary,
                                                  inputfile, arg, binaries_ent,
                                                  mode))
    return all(v == 0 for v in returncodes)


# Functions for getting the video info.


def video_length_seconds(videofile_path, binaries_ent=None):
    """ Get length of video in seconds.

    Args:
        binaries_ent: Dictionary with binaries and their path.
        videofile_path: Path to video file.

    Returns: Length of video in seconds.
    """
    if binaries_ent is None:
        global binaries
        ffprobepath = binaries["ffprobe"]
    elif type(binaries_ent) == str:
        ffprobepath = binaries_ent
    elif type(binaries_ent) == dict:
        ffprobepath = binaries_ent["ffprobe"]
    else:
        raise TypeError(
            "Passed binary can only be in format string or dictionary")

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
            videofiles_duration[videofile_path] = float(result.stdout)
            return float(result.stdout)
        except ValueError:
            raise ValueError(result.stderr.rstrip("\n"))


def video_framerate(videofile_path, binaries_ent=None):
    """ Get framerate of video in seconds.

    Args:
        binaries_ent: Dictionary with binaries and their path or string with path
                  to ffprobe.
        videofile_path: Path to video file.

    Returns: Framerate of video.
    """
    if binaries_ent is None:
        global binaries
        ffprobepath = binaries["ffprobe"]
    elif type(binaries_ent) == str:
        ffprobepath = binaries_ent
    elif type(binaries_ent) == dict:
        ffprobepath = binaries_ent["ffprobe"]
    else:
        raise TypeError(
            "Passed binary can only be in format string or dictionary")

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
            framerate = int(framerate_str.split("/")[0]) / int(
                framerate_str.split("/")[1])
            videofiles_framerate[videofile_path] = framerate
            return framerate
        except ValueError:
            raise ValueError(result.stderr.rstrip("\n"))


def video_frames(videofile_path, binaries_ent=None):
    """ Calculate number of frames of video.

    Args:
        binaries_ent: Dictionary with binaries and their path or string with path
                  to ffprobe.
        videofile_path: Path to video file.

    Returns: Number of frames of video.
    """
    return int(
        video_framerate(videofile_path, binaries_ent) *
        video_length_seconds(videofile_path, binaries_ent))


def video_stream_size(videofile_path, binaries_ent=None):
    """ Get size of video in KB.

    Args:
        binaries_ent: Dictionary with binaries and their path or string with path
                  to ffmpeg.
        videofile_path: Path to video file.

    Returns: Size of stream in KB.
    """
    if binaries_ent is None:
        global binaries
        ffmpegpath = binaries["ffprobe"]
    elif type(binaries_ent) == str:
        ffmpegpath = binaries_ent
    elif type(binaries_ent) == dict:
        ffmpegpath = binaries_ent["ffmpeg"]
    else:
        raise TypeError(
            "Passed binary can only be in format string or dictionary")

    result = subprocess.run(
        [
            ffmpegpath,
            "-hide_banner",
            "-i", videofile_path,
            "-map", "0:v:0",
            "-c", "copy",
            "-f", "null", "-"
        ],
        capture_output=True,
        text=True,
    )
    try:
        size = (result.stderr.rsplit("\n")[-2].rsplit(" ")[0].rsplit(":")[1][0: -2])
        return float(size)
    except ValueError:
        raise ValueError(result.stderr.rstrip("\n"))


def video_dimensions(videofile_path, binaries_ent=None):
    """ Get framerate of video in seconds.

    Args:
        binaries_ent: Dictionary with binaries and their path or string with path
                  to ffprobe.
        videofile_path: Path to video file.

    Returns: Framerate of video.
    """
    if binaries_ent is None:
        global binaries
        ffprobepath = binaries["ffprobe"]
    elif type(binaries_ent) == str:
        ffprobepath = binaries_ent
    elif type(binaries_ent) == dict:
        ffprobepath = binaries_ent["ffprobe"]
    else:
        raise TypeError(
            "Passed binary can only be in format string or dictionary")

    global videofiles_resolution
    try:
        resolution = videofiles_resolution[videofile_path]
        return resolution
    except KeyError:
        result = subprocess.run(
            [
                ffprobepath,
                "-v",
                "error",
                "-select_streams",
                "v:0",
                "-show_entries",
                "stream=width,height",
                "-of",
                "csv=s=x:p=0",
                videofile_path,
            ],
            capture_output=True,
            text=True,
        )
        try:
            resolution_str = str(result.stdout.split("\n")[0])
            resolution = [int(resolution_str.split("x")[0]), int(resolution_str.split("x")[1])]
            videofiles_resolution[videofile_path] = resolution_str
            return resolution_str
        except ValueError:
            raise ValueError(result.stderr.rstrip("\n"))


def video_pix_fmt(videofile_path, binaries_ent=None):
    """ Get pix_fmt of video in ffmpeg's format.

    Args:
        binaries_ent: Dictionary with binaries and their path or string with path
                  to ffprobe.
        videofile_path: Path to video file.

    Returns: String with ffmpeg pix_fmt format. (eg. "yuv420p10le")
    """
    if binaries_ent is None:
        global binaries
        ffprobepath = binaries["ffprobe"]
    elif type(binaries_ent) == str:
        ffprobepath = binaries_ent
    elif type(binaries_ent) == dict:
        ffprobepath = binaries_ent["ffprobe"]
    else:
        raise TypeError(
            "Passed binary can only be in format string or dictionary")

    global videofiles_pix_fmt
    try:
        pix_fmt = videofiles_pix_fmt[videofile_path]
        return pix_fmt
    except KeyError:
        result = subprocess.run(
            [
                ffprobepath,
                "-v",
                "error",
                "-select_streams",
                "v:0",
                "-show_entries",
                "stream=pix_fmt",
                "-of",
                "default=noprint_wrappers=1:nokey=1",
                videofile_path,
            ],
            capture_output=True,
            text=True,
        )
        return str(result.stdout.split("\n")[0])


def video_get_info_for_yuv(videofile_path, binaries_ent=None):
    return (video_framerate(videofile_path, binaries_ent),
            video_dimensions(videofile_path, binaries_ent),
            video_pix_fmt(videofile_path, binaries_ent))


def pix_fmt_bpp(pix_fmt, binaries_ent=None):
    if binaries_ent is None:
        global binaries
        ffmpegpath = binaries["ffmpeg"]
    elif type(binaries_ent) == str:
        ffmpegpath = binaries_ent
    elif type(binaries_ent) == dict:
        ffmpegpath = binaries_ent["ffmpeg"]
    else:
        raise TypeError(
            "Passed binary can only be in format string or dictionary")

    result = subprocess.run(
        [
            ffmpegpath,
            "-pix_fmts",
            "-hide_banner",
        ],
        capture_output=True,
        text=True,
    )
    line = [s for s in result.stdout.split("\n") if pix_fmt+" " in s][0]
    if line[2] == "H":
        return -1
    return int(line[-4:].lstrip())


def calculate_size_raw(num_frames, video_dimensions, pix_fmt, binaries_ent=None):
    return num_frames*int(video_dimensions.split("x")[0])*int(video_dimensions.split("x")[1])*pix_fmt_bpp(pix_fmt, binaries_ent)
