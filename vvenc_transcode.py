import os
import subprocess
import encoders_comparison_tool as enc


OUTPUT_UNSUPORTED_BY_FFMPEG = True
INPUT_FILE_TYPE = ("yuv")
OUTPUT_FILE_TYPE = "mkv"
ENCODED_FILE_TYPE = "266"
# If the encoder doesn't support the input format, then transcode in
# encoders_comparison_tool to supported format. If the format is YUV, the
# function sends back the pix_fmt, framerate and path to transcoded file.


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


def _pix_fmt_to_param(pix_fmt):
    if pix_fmt.startswith("yuv4") and pix_fmt[6] == "p":
        # VVC support only progressive scan and input file in YUV
        # InputBitDepth is for --InputBitDepth
        # ChromaFormat is for --InputChromaFormat
        # InternalBitDepth is for --InternalBitDepth
        ChromaFormat = pix_fmt[3:6]
        if pix_fmt.endswith("p"):
            InputBitDepth = 8
        elif pix_fmt.endswith("le"):
            InputBitDepth = pix_fmt[7:9]
            if InputBitDepth.endswith("l"):
                InputBitDepth = pix_fmt[7]
        InternalBitDepth = InputBitDepth
        return str(InputBitDepth), str(ChromaFormat), str(InternalBitDepth)


# Internal function
def _encode_cmd(job, inputfile_format, run):
    if job.two_pass:
        # fot two pass encoding you need to specify target bitrate.
        # QP mode is only for one pass mode.
        if(run == 1):
            cmd = [job.binary[0], "-i", job.inputfile_variant, "--Passes", "2",
                   "--Pass", "1", f"--rcstatsfile={job.job_id}_stat.json"] + list(job.args) + list(inputfile_format)
        elif(run == 2):
            cmd = [job.binary[0], "-i", job.inputfile_variant,
                   "-b", job.encodedfile, "--Passes", "2", "--Pass", "2",
                   f"--rcstatsfile={job.job_id}_stat.json"] + list(job.args) + list(inputfile_format)
    else:
        cmd = [job.binary[0], "-i", job.inputfile_variant, "-b", job.encodedfile] + list(job.args) + list(inputfile_format)
    print(" ".join(cmd))
    return cmd


# Run encode
def _encode(job, inputfile_format, run):
    cmd = _encode_cmd(job, inputfile_format, run)
    process = subprocess.Popen(
        cmd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    return process


# Run decode
def _decode_to_null(job):
    if os.name == "posix":
        nullfile = "/dev/null"
    if os.name == "nt":
        nullfile = "NUL"
    cmd = [job.binary[1], "-b", job.encodedfile, "--y4m", "-o", nullfile]
    process = subprocess.Popen(
        cmd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return process


# Run decode
def _decode_to_ffmpeg(job):
    cmd = [job.binary[1], "-b", job.encodedfile, "--y4m", "-o", "-"]
    process_vvdec = subprocess.Popen(
        cmd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    cmd = [job.binaries["ffmpeg"], "-i", "pipe:0", "-c:v", "ffv1", job.outputfile]
    process_ffmpeg = subprocess.Popen(
        cmd,
        text=True,
        stdin=process_vvdec.stdout,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return process_vvdec, process_ffmpeg


def get_input_variant(inputfile):
    # Replace for now with dummy function
    # For now have .yuv file beside input file
    return os.path.splitext(inputfile)[0] + ".yuv"


# Start transcode
def transcode_start(job):
    dimensions = enc.video_dimensions(job.inputfile)
    fps = enc.video_framerate_str(job.inputfile)
    pix_fmt = enc.video_pix_fmt(job.inputfile)
    InputBitDepth, ChromaFormat, InternalBitDepth = _pix_fmt_to_param(pix_fmt)
    inputfile_format = ["-s", dimensions, "--fps", fps,
                        "--InputBitDepth", InputBitDepth,
                        "--InputChromaFormat", ChromaFormat,
                        "--InternalBitDepth", InternalBitDepth]
    if job.two_pass:
        report_file = f"{os.path.splitext(job.outputfile)[0]}_first_pass.report"
        enc.transcode_status_update_callback(job, ["state", "first pass"])
        firstpass = _encode(job, inputfile_format, 1)
        job.PID = firstpass.pid
        frame_num = 0
        while firstpass.poll() is None:
            line = firstpass.stdout.readline().rstrip("\n")
            frame_num = transcode_get_info(job, firstpass, line, frame_num, report=report_file)
        job.PID = None
        firstpass.wait()
        if (firstpass.returncode > 0):
            raise ValueError(
                "command: {}\n failed with returncode: {}\nProgram output:\n{}"
                .format(" ".join(firstpass.job.args), firstpass.returncode,
                        firstpass.stdout.read()))

        enc.transcode_status_update_callback(job, ["state", "second pass"])
        process = _encode(job, inputfile_format, 2)
        job.PID = process.pid
        frame_num = 0
        while process.poll() is None:
            line = process.stdout.readline().rstrip("\n")
            frame_num = transcode_get_info(job, process, line, frame_num)
        process.wait()
        if (process.returncode > 0):
            raise ValueError(
                "command: {}\n failed with returncode: {}\nProgram output:\n{}"
                .format(" ".join(process.args), process.returncode,
                        process.stdout.read()))
    else:
        enc.transcode_status_update_callback(job, ["state", "running"])
        process = _encode(job, inputfile_format, 1)
        job.PID = process.pid
        frame_num = 0
        while process.poll() is None:
            line = process.stdout.readline().rstrip("\n")
            frame_num = transcode_get_info(job, process, line, frame_num)
        job.PID = None
        process.wait
        if (process.returncode > 0):
            raise ValueError(
                "command: {}\n failed with returncode: {}\nProgram output:\n{}"
                .format(" ".join(process.args), process.returncode,
                        process.stdout.read()))
    if job.measure_decode:
        enc.transcode_status_update_callback(job, ["state", "measuring decode"])
        process = _decode_to_null(job)
        job.PID = process.pid
        process.wait()
        job.PID = None
        print(process.returncode)
    enc.transcode_status_update_callback(job, ["state", "decoding and compressing"])
    process_vvdec, process_ffmpeg = _decode_to_ffmpeg(job)
    process_vvdec.wait()
    process_ffmpeg.wait()
    print(process_vvdec.returncode)
    print(process_ffmpeg.returncode)
    job.finished = True
    enc.transcode_status_update_callback(job, ["state", "finished"])
    return job.job_id, process.returncode


def transcode_clean():
    pass


def transcode_get_info_stop(fdr, fdw):
    pass


# Get info back to encoders_comparison_tool. Function must call callback function when the status changes.
def transcode_get_info(job, process, line, frame_num, report=None):
    if report is None:
        report = job.report
    if line.startswith("POC"):
        frame_num += 1
        enc.transcode_status_update_callback(job, ["frame", frame_num])
        calc = ["progress_perc", ""]
        calc[1] = format((frame_num / enc.video_frames(job.inputfile) * 100), '.2f')
        enc.transcode_status_update_callback(job, calc)
        enc.transcode_status_update_callback(job, ["progress", "running"])
    elif line.startswith(" finished"):
        enc.transcode_status_update_callback(job, ["frame", str(enc.video_frames(job.inputfile))])
        enc.transcode_status_update_callback(job, ["progress_perc", "100.00"])
        enc.transcode_status_update_callback(job, ["progress", "finished"])
    with open(report, "a") as f:
        f.write(line + "\n")
    enc.transcode_stdout_update_callback(job, line)
    return frame_num
