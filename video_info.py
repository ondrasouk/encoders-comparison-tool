import subprocess


binaries = {}
# Videofiles properties. Key is video file path.
videofiles_frame_num = {}
videofiles_duration = {}
videofiles_framerate = {}
videofiles_resolution = {}
videofiles_pix_fmt = {}
pix_fmts_bpp = {}


def set_defaults(binaries_ent):
    global binaries
    binaries = {**binaries, **binaries_ent}

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


def video_framerate_str(videofile_path, binaries_ent=None):
    """ Get framerate of video as string.

    Args:
        binaries_ent: Dictionary with binaries and their path or string with path
                  to ffprobe.
        videofile_path: Path to video file.

    Returns: Framerate of video as string of "numerator/denominator".
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

    global videofiles_framerate
    try:
        framerate_str = videofiles_framerate[videofile_path]
        return framerate_str
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
            videofiles_framerate[videofile_path] = framerate_str
            return framerate_str
        except ValueError:
            raise ValueError(result.stderr.rstrip("\n"))


def video_framerate(videofile_path, binaries_ent=None):
    """ Get framerate of video.

    Args:
        binaries_ent: Dictionary with binaries and their path or string with path
                  to ffprobe.
        videofile_path: Path to video file.

    Returns: Framerate of video as number.
    """
    global videofiles_framerate
    try:
        framerate_str = videofiles_framerate[videofile_path]
        framerate = int(framerate_str.split("/")[0]) / int(
                framerate_str.split("/")[1])
        return framerate
    except KeyError:
        framerate_str = video_framerate_str(videofile_path, binaries_ent=binaries_ent)
        framerate = int(framerate_str.split("/")[0]) / int(
            framerate_str.split("/")[1])
        videofiles_framerate[videofile_path] = framerate_str
        return framerate


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
    """ Get dimensions of video in pixels.

    Args:
        binaries_ent: Dictionary with binaries and their path or string with path
                  to ffprobe.
        videofile_path: Path to video file.

    Returns: Dimensions of video in string. e.g. "1920x1080"
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
