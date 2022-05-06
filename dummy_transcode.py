OUTPUT_UNSUPORTED_BY_FFMPEG = False
INPUT_FILE_TYPE = ("mkv", "yuv", "y4m")
OUTPUT_FILE_TYPE = "mkv"


# Start transcode
def transcode_start(job):
    pass
    return job.job_id, 0


def get_input_variant(job):
    pass


# Clean after transcode ended.
def transcode_clean(fdw):
    pass


# Optional: If the transcode_get_info has the risk of stuck, implement this function.
def transcode_get_info_stop(fdr, fdw):
    transcode_clean(fdw)


# Get info back to encoders_comparison_tool. Function must call callback function when the status changes.
def transcode_get_info(job, process, fdr):
    pass


# Test if configuration works
def transcode_check_arguments(binpath, filename, args, binaries, mode="quick"):
    return 0
