import os
import subprocess
import pickle
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import scipy as sc
import pathlib
import threading
import concurrent.futures as cf
from scipy.signal import medfilt
import csv
import tikzplotlib
import encoders_comparison_tool as enc
import video_info as vi
from bj_delta import bj_delta, bj_delta_akima


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


useage_log_suffix = "_useage.log"
psnr_log_suffix = "-psnr_logfile.txt"
ssim_log_suffix = "-ssim_logfile.txt"
vmaf_log_suffix = "-vmaf_logfile.txt"
videofiles = []
codecs = ["av1", "svtav1", "vp9", "x264", "x265", "vvc"]
codecs_short = {"av1": "AV1", "svtav1": "SVT-AV1", "vp9": "VP9", "x264": "x264", "x265": "x265", "vvc": "VVenC",}
sequences = ["Netflix Aerial yuv420p10le 60fps",
             "ShakeNDry yuv420p 30fps",
             "SunBath yuv420p10le 50fps",
             "Tree Shade yuv420p10le 30fps",
             "Sintel2 yuv420p10le 24fps",
             ]
preset = ["preset"]
top_dir = "/run/media/ondra/video/test2/"
# top_dir = "/run/media/ondra/61597e72-9c9f-4edd-afab-110602521f55/test2/"
graphics_dir = "graphs/"
sequences_short = {
    "Netflix Aerial yuv420p10le 60fps": "Aerial",
    "ShakeNDry yuv420p 30fps": "ShakeNDry",
    "SunBath yuv420p10le 50fps": "SunBath",
    "Tree Shade yuv420p10le 30fps": "Tree Shade",
    "Sintel2 yuv420p10le 24fps": "Sintel2",
}

series_labels = {
    'av1-cpu-used_3-': "AV1 cpu-used 3",
    'av1-cpu-used_4-': "AV1 cpu-used 4",
    'av1-cpu-used_5-': "AV1 cpu-used 5",
    'av1-cpu-used_6-': "AV1 cpu-used 6",
    'svtav1-preset_3-': "SVT-AV1 preset 3",
    'svtav1-preset_5-': "SVT-AV1 preset 5",
    'svtav1-preset_7-': "SVT-AV1 preset 7",
    'svtav1-preset_9-': "SVT-AV1 preset 9",
    'svtav1-preset_11-': "SVT-AV1 preset 11",
    'svtav1-preset_13-': "SVT-AV1 preset 13",
    'vp9-rc_0-': "VP9 RC 0",
    'vp9-cpu-used_0-': "VP9 cpu-used 0",
    'vp9-cpu-used_2-': "VP9 cpu-used 2",
    'vp9-cpu-used_4-': "VP9 cpu-used 4",
#    'x264-preset_ultrafast-': "x264 ultrafast",
    'x264-preset_fast-': "x264 fast",
    'x264-preset_medium-': "x264 medium",
    'x264-preset_slow-': "x264 slow",
    'x264-preset_veryslow-': "x264 veryslow",
    'x264-preset_placebo-': "x264 placebo",
    'x265-preset_ultrafast-': "x265 ultrafast",
    'x265-preset_fast-': "x265 fast",
    'x265-preset_medium-': "x265 medium",
    'x265-preset_slow-': "x265 slow",
    'x265-preset_veryslow-': "x265 veryslow",
    'vvc-preset_faster-': "VVenC faster",
    'vvc-preset_fast-': "VVenC fast",
    'vvc-preset_medium-': "VVenC medium",
}
psnr_lim = {
    "Netflix Aerial yuv420p10le 60fps": (33, 47),
    "ShakeNDry yuv420p 30fps": (33, 44),
    "Sintel2 yuv420p10le 24fps": (40, 60),
    "SunBath yuv420p10le 50fps": (35, 55),
    "Tree Shade yuv420p10le 30fps": (35, 45),
    }
ssim_lim = {
    "Netflix Aerial yuv420p10le 60fps": (0.9, 1),
    "ShakeNDry yuv420p 30fps": (0.9, 0.98),
    "Sintel2 yuv420p10le 24fps": (0.98, 1),
    "SunBath yuv420p10le 50fps": (0.94, 1),
    "Tree Shade yuv420p10le 30fps": (0.92, 0.99),
    }
msssim_lim = {
    "Netflix Aerial yuv420p10le 60fps": (0.9, 1),
    "ShakeNDry yuv420p 30fps": (0.92, 1),
    "Sintel2 yuv420p10le 24fps": (0.98, 1),
    "SunBath yuv420p10le 50fps": (0.94, 1),
    "Tree Shade yuv420p10le 30fps": (0.96, 1),
    }
vmaf_lim = {
    "Netflix Aerial yuv420p10le 60fps": (60, 100),
    "ShakeNDry yuv420p 30fps": (70, 100),
    "Sintel2 yuv420p10le 24fps": (70, 100),
    "SunBath yuv420p10le 50fps": (70, 100),
    "Tree Shade yuv420p10le 30fps": (80, 100),
    }
bitrate_lim = {
    "Netflix Aerial yuv420p10le 60fps": (0, 150),
    "ShakeNDry yuv420p 30fps": (0, 200),
    "Sintel2 yuv420p10le 24fps": (0, 45),
    "SunBath yuv420p10le 50fps": (0, 150),
    "Tree Shade yuv420p10le 30fps": (0, 200),
    }
bitrate_lim_log = {
    "Netflix Aerial yuv420p10le 60fps": (0.1, 1000),
    "ShakeNDry yuv420p 30fps": (0.1, 1000),
    "SunBath yuv420p10le 50fps": (0.1, 1000),
    "Tree Shade yuv420p10le 30fps": (0.1, 1000),
    "Sintel2 yuv420p10le 24fps": (0.1, 100),
    }
processing_lim = {
    "Netflix Aerial yuv420p10le 60fps": (0, 50000),
    "ShakeNDry yuv420p 30fps": (0, 8000),
    "SunBath yuv420p10le 50fps": (0, 5000),
    "Tree Shade yuv420p10le 30fps": (0, 12000),
    "Sintel2 yuv420p10le 24fps": (0, 12000),
    }
processing_lim_log = {
    "Netflix Aerial yuv420p10le 60fps": (1, 1000),
    "ShakeNDry yuv420p 30fps": (1, 10000),
    "SunBath yuv420p10le 50fps": (1, 1000),
    "Tree Shade yuv420p10le 30fps": (1, 1000),
    "Sintel2 yuv420p10le 24fps": (1, 1000),
    }
cpu_time_lim = {
    "Netflix Aerial yuv420p10le 60fps": (0, 200000),
    "ShakeNDry yuv420p 30fps": (0, 60000),
    "SunBath yuv420p10le 50fps": (0, 35000),
    "Tree Shade yuv420p10le 30fps": (0, 70000),
    "Sintel2 yuv420p10le 24fps": (0, 70000),
    }
cpu_time_lim_log = {
    "Netflix Aerial yuv420p10le 60fps": (0.1, 1000),
    "ShakeNDry yuv420p 30fps": (0.1, 10000),
    "SunBath yuv420p10le 50fps": (0.1, 1000),
    "Tree Shade yuv420p10le 30fps": (0.1, 1000),
    "Sintel2 yuv420p10le 24fps": (0.1, 1000),
    }
cpu_fps_lim = {
    "Netflix Aerial yuv420p10le 60fps": (0, 200),
    "ShakeNDry yuv420p 30fps": (0, 200),
    "SunBath yuv420p10le 50fps": (0, 200),
    "Tree Shade yuv420p10le 30fps": (0, 200),
    "Sintel2 yuv420p10le 24fps": (0, 200),
    }
decode_fps_lim = {
    "Netflix Aerial yuv420p10le 60fps": (0, None),
    "ShakeNDry yuv420p 30fps": (0, 60),
    "SunBath yuv420p10le 50fps": (0, 60),
    "Tree Shade yuv420p10le 30fps": (0, 60),
    "Sintel2 yuv420p10le 24fps": (0, 60),
    }
BJ1_serie = "x264-preset_placebo-"
BD_xname = "avg_bitrate_mb"
BD_ynames = ["psnr_avg", "ssim_avg", "msssim_avg", "vmaf_avg"]
BD_names = []
for n in BD_ynames:
#    BD_names.append("bd_" + n)
    BD_names.append("bd_rate_" + n)
encode_excluded_states = ["measuring decode"]
speeds_table = {
    "placebo": 0,
    "slow": 3,
    "slower": 2,
    "veryslow": 1,
    "medium": 4,
    "fast": 5,
    "faster": 6,
    "veryfast": 7,
    "superfast": 8,
    "ultrafast": 9,
    }



binaries = {
    "ffprobe": "/usr/bin/ffprobe",
    "ffmpeg": "/usr/bin/ffmpeg"
    }

vi.set_defaults(binaries)


def video_stream_size(videofile_path):
    if videofile_path.endswith(".266"):
        return os.path.getsize(videofile_path[0:-4] + ".266") / 1024  #in KiB
    log = videofile_path + ".stream_size"
    if os.path.exists(log):
        with open(log, "r") as f:
            s = f.readline()
        print("stream size hit!")
        return float(s)
    result = subprocess.run(
        [
            "ffmpeg",
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
        s = float(size)  # in KiB
        with open(log, "w") as f:
            f.write(str(s))
        return s
    except ValueError:
        raise ValueError(result.stderr.rstrip("\n"))


def video_stream_length(videofile_path):
    if videofile_path.endswith(".266"):
        videofile = videofile_path[:-4] + ".mkv"
    else:
        videofile = videofile_path
    log = videofile + ".stream_length"
    if os.path.exists(log):
        with open(log, "r") as f:
            s = f.readline()
        print("stream length hit!")
        return float(s)
    result = vi.video_length_seconds(videofile)
    with open(log, "w") as f:
        f.write(str(result))
    return result


def video_stream_frames(videofile_path):
    if videofile_path.endswith(".266"):
        videofile = videofile_path[:-4] + ".mkv"
    else:
        videofile = videofile_path
    log = videofile + ".stream_frames"
    if os.path.exists(log):
        with open(log, "r") as f:
            s = f.readline()
        print("stream framenum hit!")
        return int(s)
    result = vi.video_frames(videofile)
    with open(log, "w") as f:
        f.write(str(result))
    return result


def series_label(key, sequence=None):
    if sequence is None or sequence in key:
        k = series_labels.keys()
        for s in (s for s in k if s in key):
            return series_labels[s]
    raise KeyError

'''
def simple_plot(x, y, xlabel, ylabel, savefile, minxlim=True):
    i1, ax1 = plt.subplots()

    plt.plot(x, y)
    ax1.set(xlabel=xlabel, ylabel=ylabel)

    if minxlim:
        ax1.set_xlim(left=min(x), right=max(x))
    ax1.grid()

    plt.savefig(f"{savefile}.svg")
    plt.savefig(f"{savefile}.pgf")
    tikzplotlib.save(f"{savefile}.tex")
    plt.close(i1)


def composite_plot(mxy, mlegend, xlabel, ylabel, savefile, xlim=None, ylim=None):
    i1, ax1 = plt.subplots()

    i = enc.count()
    for m in mxy:
        t = zip(*m)
        x, y = [list(t) for t in t]
        plt.plot(x, y, label=mlegend[next(i)], marker="+")
    ax1.set(xlabel=xlabel, ylabel=ylabel)
    plt.legend()

    if xlim is True:
        ax1.set_xlim(left=min(x), right=max(x))
    elif xlim is not None:
        ax1.set_xlim(left=xlim[0], right=xlim[1])
    if ylim is True:
        ax1.set_ylim(bottom=min(y), top=max(y))
    elif ylim is not None:
        ax1.set_ylim(bottom=ylim[0], top=ylim[1])
    ax1.grid()

    p = os.path.split(savefile)
    enc.create_dir(p[0] + '/svg/')
    enc.create_dir(p[0] + '/png/')
    enc.create_dir(p[0] + '/tex/')
    plt.savefig(f"{p[0] + '/svg/' + p[1]}.svg")
    plt.savefig(f"{p[0] + '/png/' + p[1]}.png")
    tikzplotlib.save(f"{p[0] + '/tex/' + p[1]}.tex")
    plt.close(i1)


def composite_plot_smooth(mxy, mlegend, xlabel, ylabel, savefile, xlim=None, ylim=None):
    i1, ax1 = plt.subplots()

    i = enc.count()
    for m in mxy:
        t = zip(*m)
        x, y = [list(t) for t in t]
        c = plt.scatter(x, y, label=mlegend[next(i)], marker="+")
        colr = c.get_facecolor()[0]
        lx = np.log(x)
        p = sc.interpolate.Akima1DInterpolator(lx, y)
        x_smooth = np.linspace(min(x), max(x), 1000)
        y_smooth = p(np.log(x_smooth))
        plt.plot(x_smooth, y_smooth, color=colr)
    ax1.set(xlabel=xlabel, ylabel=ylabel)
    plt.legend()

    if xlim is True:
        ax1.set_xlim(left=x.min(), right=x.max())
    elif xlim is not None:
        ax1.set_xlim(left=xlim[0], right=xlim[1])
    if ylim is True:
        ax1.set_ylim(bottom=y.min(), top=y.max())
    elif ylim is not None:
        ax1.set_ylim(bottom=ylim[0], top=ylim[1])
    ax1.grid()

    p = os.path.split(savefile)
    enc.create_dir(p[0] + '/svg/')
    enc.create_dir(p[0] + '/png/')
    enc.create_dir(p[0] + '/tex/')
    plt.savefig(f"{p[0] + '/svg/' + p[1]}.svg")
    plt.savefig(f"{p[0] + '/png/' + p[1]}.png")
    tikzplotlib.save(f"{p[0] + '/tex/' + p[1]}.tex")
    plt.close(i1)
'''


def plot_graphs(data, sequence=None, codec=None):
    if sequence is None and codec is None:
        out = graphics_dir
    elif sequence is None:
        out = graphics_dir + codec + "/"
    elif codec is None:
        out = graphics_dir + sequences_short[sequence] + "/"
    else:
        out = graphics_dir + sequences_short[sequence] + "/" + codec + "/"
    lower_right = 4
    d = df_to_plot(data, "avg_bitrate_mb", "psnr_avg")
    composite_plot(d, "Bitrate [Mbit/s]", "PSNR (YUV) [dB]", out + "psnr", xlim=bitrate_lim[sequence], ylim=psnr_lim[sequence], legend_loc=lower_right)
    composite_plot(d, "Bitrate [Mbit/s]", "PSNR (YUV) [dB]", out + "psnr_log", ylim=psnr_lim[sequence], xlog=True, legend_loc=lower_right)
    d = df_to_plot(data, "avg_bitrate_mb", "ssim_avg")
    composite_plot(d, "Bitrate [Mbit/s]", "SSIM", out + "ssim", xlim=bitrate_lim[sequence], ylim=ssim_lim[sequence], legend_loc=lower_right)
#    composite_plot(d, "Bitrate [Mbit/s]", "SSIM", out + "ssim_log", ylim=ssim_lim[sequence], xlog=True, legend_loc=lower_right)
    d = df_to_plot(data, "avg_bitrate_mb", "msssim_avg")
    composite_plot(d, "Bitrate [Mbit/s]", "MS-SSIM", out + "msssim", xlim=bitrate_lim[sequence], ylim=msssim_lim[sequence], legend_loc=lower_right)
#    composite_plot(d, "Bitrate [Mbit/s]", "MS-SSIM", out + "msssim_log", ylim=msssim_lim[sequence], xlog=True, legend_loc=lower_right)
    d = df_to_plot(data, "avg_bitrate_mb", "vmaf_avg")
    composite_plot(d, "Bitrate [Mbit/s]", "VMAF", out + "vmaf", xlim=bitrate_lim[sequence], ylim=vmaf_lim[sequence], legend_loc=lower_right)
#    composite_plot(d, "Bitrate [Mbit/s]", "VMAF", out + "vmaf_log", ylim=vmaf_lim[sequence], xlog=True, legend_loc=lower_right)
    d = df_to_plot(data, "avg_bitrate_mb", "decode_time_fps")
    composite_plot(d, "Bitrate [Mbit/s]", "Rychlost dekódování [frame/s]", out + "decode", ylim=(0, None), xlim=bitrate_lim_log[sequence], xlog=True)
    d = df_to_plot(data, "avg_bitrate_mb", "total_time_fps")
    composite_plot(d, "Bitrate [Mbit/s]", "Procesorový čas [s/frame]", out + "encode", ylim=(0.1, None), xlim=bitrate_lim_log[sequence], xlog=True, ylog=True)


def df_to_plot(data, x_name, y_name):
    tables = [t[[x_name, y_name]].rename(columns={x_name: "x", y_name: "y"}).sort_values(by="x") for t in list(data["table"])]
    l = list(data["label"])
    s = list(data["speed"])
    lt = zip(l, tables, s)
    for m in lt:
        setattr(m[1], "label", m[0])
        setattr(m[1], "speed", m[2])
    return tables


def df_to_plot2(data, x_name, y_name):
    tables = [data[[x_name, y_name]].rename(columns={x_name: "x", y_name: "y"}).loc[data["codec"] == s].sort_values(by="x") for s in codecs]
    lt = zip(codecs, tables)
    for m in lt:
        setattr(m[1], "label", codecs_short[m[0]])
    return tables


#def composite_plot(data, xlabel, ylabel, savefile, xlim=None, ylim=None, log_inter=True, xlog=False, ylog=False, smooth=True, xlogscalar=False, ylogscalar=False, legend_loc=None, tikz_before=True):
    #i1, ax1 = plt.subplots()
    #if not (xlog or ylog):
        #tikz_before = False
    #if xlog:
        #ax1.set_xscale('log')
        #ax1.grid(True, which="both")
        #if xlogscalar:
            #ax1.xaxis.set_major_formatter(matplotlib.ticker.ScalarFormatter())
    #else:
        #ax1.set_xscale('linear')
        #ax1.grid(True)
    #if ylog:
        #ax1.set_yscale('log')
        #ax1.grid(True, which="both")
        #if ylogscalar:
            #ax1.yaxis.set_major_formatter(matplotlib.ticker.ScalarFormatter())
    #else:
        #ax1.set_yscale('linear')
        #ax1.grid(True)
    #for table in data:
        #if smooth:
            #c = plt.scatter(table.x, table.y, label=table.label, marker="+")
            #colr = c.get_facecolor()[0]
            #if log_inter:
                #lx = np.log(table.x)
                #p = sc.interpolate.Akima1DInterpolator(lx, table.y)
                #x_smooth = np.logspace(np.log10(min(table.x)), np.log10(max(table.x)), 200)
            #else:
                #lx = table.x
                #p = sc.interpolate.Akima1DInterpolator(lx, table.y)
                #x_smooth = np.linspace(min(table.x), max(table.x), 200)
            #y_smooth = p(np.log(x_smooth))
            #plt.plot(x_smooth, y_smooth, color=colr)
        #else:
            #plt.plot(table.x, table.y, label=table.label, marker="+")
    #ax1.set(xlabel=xlabel, ylabel=ylabel)
    #if legend_loc is None:
        #ax1.legend()
    #else:
        #ax1.legend(loc=legend_loc)

    #if xlim is True:
        #ax1.set_xlim(left=table.x.min(), right=table.x.max())
    #elif xlim is not None:
        #ax1.set_xlim(left=xlim[0], right=xlim[1])
    #if ylim is True:
        #ax1.set_ylim(bottom=table.y.min(), top=table.y.max())
    #elif ylim is not None:
        #ax1.set_ylim(bottom=ylim[0], top=ylim[1])

    #p = os.path.split(savefile)
    #enc.create_dir(p[0] + '/svg/')
    #enc.create_dir(p[0] + '/png/')
    #enc.create_dir(p[0] + '/tex/')
    #if tikz_before:
        #tikzplotlib.save(f"{p[0] + '/tex/' + p[1]}.tex")
    #plt.savefig(f"{p[0] + '/svg/' + p[1]}.svg")
    #plt.savefig(f"{p[0] + '/png/' + p[1]}.png")
    #if not tikz_before:
        #tikzplotlib.save(f"{p[0] + '/tex/' + p[1]}.tex")
    #plt.close(i1)


def composite_plot(data, xlabel, ylabel, savefile, xlim=None, ylim=None, log_inter=True, xlog=False, ylog=False, smooth=True, xlogscalar=False, ylogscalar=False, legend_loc=None, tikz_before=True):
    plt.figure()
    plt.axis()
    if not (xlog or ylog):
        tikz_before = False
    if xlog:
        plt.xscale('log')
        plt.grid(True, which="both")
#        if xlogscalar:
#            plt.xaxis.set_major_formatter(matplotlib.ticker.ScalarFormatter())
    else:
        plt.xscale('linear')
        plt.grid(True)
    if ylog:
        plt.yscale('log')
        plt.grid(True, which="both")
#        if ylogscalar:
#            plt.yaxis.set_major_formatter(matplotlib.ticker.ScalarFormatter())
    else:
        plt.yscale('linear')
        plt.grid(True)
    for table in data:
        if smooth:
            c = plt.scatter(table.x, table.y, label=table.label, marker="+")
            colr = c.get_facecolor()[0]
            if log_inter:
                lx = np.log(table.x)
                p = sc.interpolate.Akima1DInterpolator(lx, table.y)
                x_smooth = np.logspace(np.log10(min(table.x)), np.log10(max(table.x)), 200)
            else:
                lx = table.x
                p = sc.interpolate.Akima1DInterpolator(lx, table.y)
                x_smooth = np.linspace(min(table.x), max(table.x), 200)
            y_smooth = p(np.log(x_smooth))
            plt.plot(x_smooth, y_smooth, color=colr)
        else:
            plt.plot(table.x, table.y, label=table.label, marker="+")
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.legend(loc=legend_loc)

    if xlim is True:
        plt.xlim(left=table.x.min(), right=table.x.max())
    elif xlim is not None:
        plt.xlim(left=xlim[0], right=xlim[1])
    if ylim is True:
        plt.ylim(bottom=table.y.min(), top=table.y.max())
    elif ylim is not None:
        plt.ylim(bottom=ylim[0], top=ylim[1])

    p = os.path.split(savefile)
    enc.create_dir(p[0] + '/svg/')
    enc.create_dir(p[0] + '/png/')
    enc.create_dir(p[0] + '/tex/')
    if tikz_before:
        tikzplotlib.save(f"{p[0] + '/tex/' + p[1]}.tex")
    plt.savefig(f"{p[0] + '/svg/' + p[1]}.svg")
    plt.savefig(f"{p[0] + '/png/' + p[1]}.png")
    if not tikz_before:
        tikzplotlib.save(f"{p[0] + '/tex/' + p[1]}.tex")
    plt.close()


def df_to_latex_table(values, save_path):
    pass


def calc_bj(mxy_o, mlegend_o, bd_metric_legend, bd_rate_legend):
    mxy = mxy_o.copy()
    mlegend = mlegend_o.copy()
    xy1 = mxy[mlegend.index(BJ1_serie)]
    t1 = zip(*xy1)
    x1, y1 = [list(t1) for t1 in t1]
    mxy.remove(xy1)
    mlegend.remove(BJ1_serie)
    i = enc.count()
    for m in mxy:
        t = zip(*m)
        x, y = [list(t) for t in t]
        bd_metric = bj_delta(x1, y1, x, y, mode=0)
        bd_rate = bj_delta(x1, y1, x, y, mode=1)
        l = mlegend[next(i)]
        print(f"{l}: BD-{bd_metric_legend}: {bd_metric}%")
        print(f"{l}: BD-{bd_rate_legend}: {bd_rate}%")

def formatter1(x):
    s = ('%1.2f' % x).replace(".",",") + "\,\%"
    return s

def formatter2(x):
    s = ('%1.2f' % x).replace(".",",") + "\%"
    if x > 0:
        s = "\cellcolor{red!25}" + s
    elif x < 0:
        s = "\cellcolor{green!25}" + s
    return s


def calc_bj_cross_to_table(mxy_o, mlegend_o, bd_metric_legend, bd_rate_legend):
    table_metric = pd.DataFrame(np.zeros((len(mlegend_o), len(mlegend_o))), columns=mlegend_o, index=mlegend_o)
    table_rate = pd.DataFrame(np.zeros((len(mlegend_o), len(mlegend_o))), columns=mlegend_o, index=mlegend_o)
    for mleg in mlegend_o:
        mxy = mxy_o.copy()
        mlegend = mlegend_o.copy()
        xy1 = mxy[mlegend.index(mleg)]
        t1 = zip(*xy1)
        x1, y1 = [list(t1) for t1 in t1]
        mxy.remove(xy1)
        mlegend.remove(mleg)
        i = enc.count()
        for m in mxy:
            t = zip(*m)
            x, y = [list(t) for t in t]
            bd_metric = bj_delta(x1, y1, x, y, mode=0)
            bd_rate = bj_delta(x1, y1, x, y, mode=1)
            l = mlegend[next(i)]
            table_metric.loc[l, mleg] = bd_metric
            table_rate.loc[l, mleg] = bd_rate
#    print(table_metric.to_latex(float_format="%.2f", decimal=","))
#    print(table_rate.to_latex(float_format="%.2f"))
    return table_metric, table_rate


'''
def calc_bj_akima(dftable, x_name, y_name, bd_metric_legend, bd_rate_legend):
    xy1 = mxy[mlegend.index(BJ1_serie)]
    t1 = zip(*xy1)
    x1, y1 = [list(t1) for t1 in t1]
    mxy.remove(xy1)
    mlegend.remove(BJ1_serie)
    i = enc.count()
    for m in mxy:
        t = zip(*m)
        x, y = [list(t) for t in t]
        bd_metric = bj_delta_akima(x1, y1, x, y, mode=0)
        bd_rate = bj_delta_akima(x1, y1, x, y, mode=1)
        l = mlegend[next(i)]
        print(f"{l}: BD-{bd_metric_legend}: {bd_metric}%")
        print(f"{l}: BD-{bd_rate_legend}: {bd_rate}%")
'''


def calc_bj_akima(data, x_name, y_name, bd_metric_legend, bd_rate_legend):
    df = data.copy()
    for t in df.itertuples():
        t.table.rename(columns={x_name: "x", y_name: "y"}).sort_values(by="x")
    df
    bd_metric = bj_delta_akima(x1, y1, x, y, mode=0)
    bd_rate = bj_delta_akima(x1, y1, x, y, mode=1)


def read_table_kcolv(logpath):
    with open(logpath, "r") as f:
        firstline = next(f).rstrip(" \n")
    columns = []
    for x in firstline.rsplit(" "):
        columns.append(x.rsplit(":")[0])
    r = range(len(columns))
    table = pd.read_table(logpath, names=columns, usecols=list(r), sep=" ",
                          converters={k: lambda x: (x.rsplit(":")[1]) for k in r})
    return table.apply(pd.to_numeric)


class PSNR_values:
    def __init__(self, logpath):
        self.logpath = logpath
        table = read_table_kcolv(self.logpath)
        self.n = table.n
        self.mse_avg = table.mse_avg
        self.mse_y = table.mse_y
        self.mse_u = table.mse_u
        self.mse_v = table.mse_v
        self.psnr_avg = table.psnr_avg
        self.psnr_y = table.psnr_y
        self.psnr_u = table.psnr_u
        self.psnr_v = table.psnr_v
        self.mse_avg_avg = np.average(self.mse_avg)
        self.mse_y_avg = np.average(self.mse_y)
        self.mse_u_avg = np.average(self.mse_u)
        self.mse_v_avg = np.average(self.mse_v)
        self.psnr_avg_avg = np.average(self.psnr_avg)
        self.psnr_y_avg = np.average(self.psnr_y)
        self.psnr_u_avg = np.average(self.psnr_u)
        self.psnr_v_avg = np.average(self.psnr_v)


class SSIM_values:
    def __init__(self, logpath):
        self.logpath = logpath
        names = ("n", "Y", "U", "V", "All", "unnorm")
        table = pd.read_table(self.logpath, names=names, sep=" ",
                              converters={k: lambda x: (x.rsplit(":")[1]) for k in range(5)})
        table.unnorm = table.unnorm.str.slice(start=1, stop=-1)
        table = table.apply(pd.to_numeric)
        self.n = table.n
        self.Y = table.Y
        self.U = table.U
        self.V = table.V
        self.All = table.All
        self.unnorm = table.unnorm  # unnorm = 10*log10(1-All)
        self.Y_avg = np.average(self.Y)
        self.U_avg = np.average(self.U)
        self.V_avg = np.average(self.V)
        self.All_avg = np.average(self.All)
        self.unnorm_avg = np.average(self.unnorm)


class VMAF_values:
    def __init__(self, logpath):
        self.logpath = logpath
        table = pd.read_table(logpath, sep=",")
        table = table.loc[:, ~table.columns.str.contains('^Unnamed')]
        self.table = table
        self.vmaf_avg = table.vmaf.mean()


class Useage_values:
    def __init__(self, logpath):
        self.logpath = logpath
        with open(logpath, "r") as log:
            firstline = next(log)
        self.row_names = firstline.rsplit(",")[0:-1]
        table = pd.read_csv(self.logpath)
        self.table = table
        self.state_names = list(table.state.unique())
        total_time = 0
        total_cpu_time = 0
        for state in [x for x in self.state_names if x not in encode_excluded_states]:
            for row in self.row_names:
                if row == "state":
                    pass
                else:
                    arr = np.array(table[row][table.index[table['state'] == state]])
                    setattr(self, state + "_" + row, arr)
            cpu_time_user = getattr(self, state + "_cpu_time_user")
            cpu_time_user = np.append(np.array([0]), cpu_time_user)
            cpu_time_system = getattr(self, state + "_cpu_time_system")
            cpu_time_system = np.append(np.array([0]), cpu_time_system)
            cpu_time_total = cpu_time_user + cpu_time_system
            setattr(self, state + "_cpu_time_total", cpu_time_total)
            cpu_time_diff = np.ediff1d(cpu_time_total)
            time = np.append(np.array([0]), getattr(self, state + "_time"))
            time_diff = np.ediff1d(time)
            cpu_percent_calc = cpu_time_diff / time_diff
            setattr(self, state + "_cpu_percent_calc", cpu_percent_calc)
            total_time += time[-1]
            total_cpu_time += cpu_time_total[-1]
        self.total_time = total_time
        self.total_cpu_time = total_cpu_time
        cpu_time_diff = np.ediff1d(np.append(np.array([0]), np.array(table.cpu_time_user + table.cpu_time_system)))
        time_diff = np.ediff1d(np.append(np.array([0]), np.array(table.time)))
        cpu_time_int = np.sum(cpu_time_diff * time_diff)
        self.cpu_usage_avg = cpu_time_int / total_time
        self.max_RSS = self.table.RSS.max()
        self.perc_RSS = self.table.RSS.quantile(0.9)
        self.mean_RSS = self.table.RSS.mean()
        self.med_RSS = self.table.RSS.median()
        for row in self.row_names:
            if row == "state":
                pass
            else:
                arr = np.array(table[row][table.index[table['state'] == "measuring decode"]])
                setattr(self, "decode_row_" + row, arr)
        self.decode_time = self.decode_row_time[-1]
        self.decode_cpu_time = self.decode_row_cpu_time_user[-1] + self.decode_row_cpu_time_system[-1]


class VideoFile:
    def __init__(self, videofilepath):
        self.videofilepath = videofilepath
        self.basename = os.path.basename(videofilepath)
        self.path_without_ext = os.path.splitext(videofilepath)[0]
        if os.path.exists(self.path_without_ext + ".266"):
            self.videofilepath = self.path_without_ext + ".266"
        self.useage_log_path = self.path_without_ext + useage_log_suffix
        if not os.path.isfile(self.useage_log_path):
            print(f"File not found: {self.useage_log_path}")
            self.useage_log_path = None
        self.psnr_log_path = self.path_without_ext + psnr_log_suffix
        if not os.path.isfile(self.psnr_log_path):
            print(f"File not found: {self.psnr_log_path}")
            self.psnr_log_path = None
        self.ssim_log_path = self.path_without_ext + ssim_log_suffix
        if not os.path.isfile(self.ssim_log_path):
            print(f"File not found: {self.ssim_log_path}")
            self.ssim_log_path = None
        self.vmaf_log_path = self.path_without_ext + vmaf_log_suffix
        if not os.path.isfile(self.vmaf_log_path):
            print(f"File not found: {self.vmaf_log_path}")
            self.vmaf_log_path = None
        self.topserie = os.path.split(os.path.split(self.videofilepath)[0])[1]
        # eg. /path/to/video/av1/cpu-used_4/ShakeNDry/ShakeNDry-crf10.mkv -> ShakeNDry
        for c in codecs:
            if c in videofilepath:
                self.codec = c
        s = os.path.split(os.path.split(self.videofilepath)[0])[0]
        # eg. /path/to/video/av1/cpu-used_4/ShakeNDry -> /path/to/video/av1/cpu-used_4
        self.serie = s[s.index(self.codec)+len(self.codec)+1:].replace("/", "-") + "-" + self.topserie
        self.label = s[s.index(self.codec)+len(self.codec)+1:].replace("/", "-")
        self.codec_serie = self.codec + "-" + self.serie

    def load_log(self):
        with cf.ThreadPoolExecutor() as executor:
            if self.psnr_log_path is not None:
                psnr = executor.submit(PSNR_values, self.psnr_log_path)
            if self.ssim_log_path is not None:
                ssim = executor.submit(SSIM_values, self.ssim_log_path)
            if self.vmaf_log_path is not None:
                vmaf = executor.submit(VMAF_values, self.vmaf_log_path)
            if self.useage_log_path is not None:
                useage = executor.submit(Useage_values, self.useage_log_path)

            if self.psnr_log_path is not None:
                self.psnr = psnr.result()
            if self.ssim_log_path is not None:
                self.ssim = ssim.result()
            if self.vmaf_log_path is not None:
                self.vmaf = vmaf.result()
            if self.useage_log_path is not None:
                self.useage = useage.result()

    def load_stream_size(self):
        self.bitstream_size = video_stream_size(self.videofilepath)
        self.total_length = video_stream_length(self.videofilepath)
        self.avg_bitrate = (8 * self.bitstream_size) * 1024 / self.total_length
        self.avg_bitrate_mb = self.avg_bitrate / 1024 / 1024
        self.total_frames = video_stream_frames(self.videofilepath)
        self.total_length = video_stream_length(self.videofilepath)
        self.total_time_fps = self.useage.total_time / self.total_frames
        self.total_cpu_time_fps = self.useage.total_cpu_time / self.total_frames
        self.decode_time_fps = self.total_frames / self.useage.decode_time
        self.decode_cpu_time_fps = self.total_frames / self.useage.decode_cpu_time


def async_load(f):
    print(f"{f.videofilepath}")
    f.load_log()
    f.load_stream_size()
    print(f"{f.videofilepath}:\tPSNR: {f.psnr.psnr_avg_avg}\tSSIM: {f.ssim.All_avg}\tVMAF: {f.vmaf.vmaf_avg}")
    return f


class DataSerie:
    def __init__(self, serie):
        self.serie = serie
        try:
            self.label = series_label(serie)
        except KeyError:
            self.label = serie
        print(f"DataSerie: {serie}: {self.label}")
        self.data = []
        self.n = []
        self.psnr_avg = []
        self.mse_avg = []
        self.ssim_avg = []
        self.msssim_avg = []
        self.vmaf_avg = []
        self.cpu_time = []
        self.total_time = []
        self.cpu_time_fps = []
        self.total_time_fps = []
        self.decode_cpu_time_fps = []
        self.decode_time_fps = []
        self.avg_bitrate = []
        self.avg_bitrate_mb = []
        self.max_RSS = []
        self.med_RSS = []
        self.perc_RSS = []

    def add_entry(self, entry):
        self.data.append(entry)
        self.frames = entry.total_frames
        self.n.append(max(entry.psnr.n))
        self.psnr_avg.append(entry.psnr.psnr_avg_avg)
        self.mse_avg.append(entry.psnr.mse_avg)
        self.ssim_avg.append(entry.ssim.All_avg)
        self.msssim_avg.append(entry.vmaf.table.ms_ssim.mean())
        self.vmaf_avg.append(entry.vmaf.vmaf_avg)
        self.cpu_time.append(entry.useage.total_cpu_time)
        self.total_time.append(entry.useage.total_time)
        self.cpu_time_fps.append(entry.total_cpu_time_fps)
        self.total_time_fps.append(entry.total_time_fps)
        self.decode_cpu_time_fps.append(entry.decode_cpu_time_fps)
        self.decode_time_fps.append(entry.decode_time_fps)
        self.avg_bitrate.append(entry.avg_bitrate)
        self.avg_bitrate_mb.append(entry.avg_bitrate_mb)
        self.max_RSS.append(entry.useage.max_RSS)
        self.med_RSS.append(entry.useage.med_RSS)
        self.perc_RSS.append(entry.useage.perc_RSS)

    def make_df(self):
        d = {'n': self.n, 'psnr_avg': self.psnr_avg, 'mse_avg': self.mse_avg,
             'ssim_avg': self.ssim_avg, 'msssim_avg': self.msssim_avg,
             'vmaf_avg': self.vmaf_avg, 'cpu_time': self.cpu_time,
             'total_time': self.total_time, 'cpu_time_fps': self.cpu_time_fps,
             'total_time_fps': self.total_time_fps,
             'decode_cpu_time_fps': self.decode_cpu_time_fps,
             'decode_time_fps': self.decode_time_fps,
             'avg_bitrate': self.avg_bitrate,
             'avg_bitrate_mb': self.avg_bitrate_mb,
             'max_RSS': self.max_RSS, 'med_RSS': self.med_RSS,
             'perc_RSS': self.perc_RSS, }
        self.table = pd.DataFrame(data=d)
        setattr(self.table, "serie", self.serie)
        setattr(self.table, "label", self.label)


class DataStr:
    def __init__(self):
        self.series = []
        self.serie_names = []
        self.codecs = []
        self.sequences = []
        self.labels = []
        self.speed = []
        self.codec_speed = []

    def add_serie(self, serie):
        self.series.append(serie.table)
        self.serie_names.append(serie.table.serie)
        self.codecs.append(serie.serie.split("-")[0])
        self.sequences.append(serie.serie.split("-")[-1])
        self.labels.append(serie.label)
        speed = None
        print(serie.table.serie)
        k = speeds_table.keys()
        for s in k:
            if s in serie.table.serie:
                speed = speeds_table[s]
        s = serie.table.serie
        if "-cpu-used_" in serie.table.serie and speed is None:
            speed = int(s.rsplit("-cpu-used_")[1].rsplit("-")[0])
        if "-preset_" in serie.table.serie and speed is None:
            speed = int(s.rsplit("-preset_")[1].rsplit("-")[0])
        self.speed.append(speed)
        self.codec_speed.append(serie.serie.split("-")[0] + "-" + str(speed))

    def make_df(self):
        short_sequence_names = [sequences_short[i] for i in self.sequences]
        d = {"serie": self.serie_names,
             "codec": self.codecs,
             "sequence": self.sequences,
             "sequence_short": short_sequence_names,
             "label": self.labels,
             "speed": self.speed,
             "codecspeed": self.codec_speed,
             "table": self.series, }
        self.table = pd.DataFrame(data=d).sort_values(["speed", "serie"])
        self.table["reference"] = [BJ1_serie in s for s in list(self.table["serie"])]
        self.bd_ref = self.table.loc[self.table["reference"] == True]
        self.table["cpu_time_avg"] = 0.0
        self.table["time_avg"] = 0.0
        self.table["cpu_time_avg_rel"] = 100.0
        self.table["time_avg_rel"] = 100.0
        for serie in self.table.itertuples():
            self.table.loc[serie.Index, "cpu_time_avg"] = serie.table.cpu_time.mean()
            self.table.loc[serie.Index, "time_avg"] = serie.table.total_time.mean()
            self.table.loc[serie.Index, "codec_short"] = codecs_short[serie.codec]
        for sequence in sequences:
            table = self.table.loc[(self.table["sequence"] == sequence) & (self.table["reference"] == False)]
            bd_ref = self.bd_ref.loc[self.bd_ref["sequence"] == sequence]
            for serie in table.itertuples():
                self.table.loc[serie.Index, "cpu_time_avg_rel"] = 100 * serie.table.cpu_time.mean() / bd_ref.table.to_list()[0].cpu_time.mean()
                self.table.loc[serie.Index, "time_avg_rel"] = 100 * serie.table.total_time.mean() / bd_ref.table.to_list()[0].total_time.mean()
                for yname in BD_ynames:
                    v1 = bd_ref.table.to_list()[0].loc[:, [BD_xname, yname]].sort_values(by=BD_xname)
                    v2 = serie.table.loc[:, [BD_xname, yname]].sort_values(by=BD_xname)
                    x1 = list(v1[BD_xname])
                    y1 = list(v1[yname])
                    x = list(v2[BD_xname])
                    y = list(v2[yname])
                    if np.any(~np.diff(y1).astype(bool)):
                        for i in range(len(y1)-1):
                            if(y1[i] == y1[i+1]):
                                y1[i+1] += 0.000001
                    if np.any(~np.diff(y).astype(bool)):
                        for i in range(len(y)-1):
                            if(y[i] == y[i+1]):
                                y[i+1] += 0.000001
                    self.table.loc[serie.Index, "bd_" + yname] = bj_delta_akima(x1, y1, x, y, mode=0)
                    self.table.loc[serie.Index, "bd_rate_" + yname] = bj_delta_akima(x1, y1, x, y, mode=1)
        self.table = self.table.fillna(0.0)

    def make_bj_plot(self):
        self.table = self.table.sort_values(["sequence", "codec", "speed"])
        for sequence in sequences:
            print(sequence)
            table = self.table.loc[datastr.table["sequence"] == sequence]
            out = graphics_dir + sequences_short[sequence] + "/"
            for yname in BD_names:
                df = df_to_plot2(table, "cpu_time_avg_rel", yname)
                #composite_plot(df, "Relativní průměrný procesorový čas [%]", "BD-rate [%]", out + yname + "_cpu", xlim=cpu_time_lim_log[sequence], xlog=True, smooth=False, xlogscalar=True)
                df = df_to_plot2(table, "time_avg_rel", yname)
                #composite_plot(df, "Relativní průměrný čas zpracování [%]", "BD-rate [%]", out + yname, xlim=processing_lim_log[sequence], xlog=True, smooth=False, xlogscalar=True)
        #t = self.table.groupby(by="codecspeed").mean()


###############################################################################
# Code for graphing starts from here
###############################################################################

data_pickle = top_dir + "data.pkl"

if os.path.exists(data_pickle):
    with open(data_pickle, 'rb') as inp:
        videofiles_paths = pickle.load(inp)
else:
    videofiles_paths = []

    print("Finding log files:\n")

    for directory in os.walk(top_dir):
        if directory[2] != []:
            for f in directory[2]:
                if f.endswith(".mkv"):
                    videofiles_paths.append(VideoFile(os.path.join(directory[0], f)))

    print("Reading log files:\n")
    with cf.ProcessPoolExecutor(max_workers=12) as executor:
        futures = tuple(executor.submit(async_load, f) for f in videofiles_paths)

    videofiles_paths = []

    for f in futures:
        videofiles_paths.append(f.result())
    with open(data_pickle, 'wb') as outp:
        pickle.dump(videofiles_paths, outp)

#print("Rendering graphs:\n")

#    simple_plot(np.array(np.array([0]),np.array(f.useage.table.time)),
#                np.array(np.array([0]),np.array(f.useage.table.RSS/(1024*1024))),
#                "Time [s]", "RAM usage (RSS) [MiB]", f.path_without_ext + "_RSS")
print("Rendering composite graphs:\n")

series = []
codec_series = []
used_codecs = []
for f in videofiles_paths:
    series.append(f.serie)
    codec_series.append(f.codec_serie)
    used_codecs.append(f.codec)
series = list(set(series))
codec_series = list(set(codec_series))
used_codecs = list(set(used_codecs))
print(series)
print(codec_series)
print(used_codecs)

data = []
for serie in codec_series:
    data.append(DataSerie(serie))
    for f in (f for f in videofiles_paths if serie == f.codec_serie):
        data[-1].add_entry(f)

for serie in data:
    serie.make_df()

# sort by serie name
l, data = zip(*sorted(zip([d.serie for d in data], data)))
del l

print(data[0].avg_bitrate)
print(data[0].msssim_avg)

datastr = DataStr()

for serie in data:
    datastr.add_serie(serie)
datastr.make_df()
datastr.make_bj_plot()

# datastr.table.loc[datastr.table["codec"] == "av1"]
# vybrat jen řádky, kterém mají ve sloupci tuto hodnotu

# d = data[0].table[["avg_bitrate_mb", "psnr_avg"]].sort_values(by=["avg_bitrate_mb"])

print("\nplotting by sequence, codec")
for sequence in sequences:
    print(sequence)
    table = datastr.table.loc[datastr.table["sequence"] == sequence]
#    plot_graphs(table, sequence=sequence)
    for codec in codecs:
        table2 = table.loc[table["codec"] == codec]
#        plot_graphs(table2, sequence=sequence, codec=codec)

rdfb_list = []
print("\nplotting by sequence, and most slow in codec")
for sequence in sequences:
    print(sequence)
    rdf_list = []
    table = datastr.table.loc[datastr.table["sequence"] == sequence]
    for codec in codecs:
        table2 = table.loc[table["codec"] == codec]
        rdf_list.append(table2.loc[table2["speed"].idxmin()])
    table2 = pd.concat(rdf_list)
#    plot_graphs(table2, sequence=sequence)
    table3 = pd.DataFrame(rdf_list)
    rdfb_list.append(table3)

table = pd.concat(rdfb_list, axis=0)

for yname in BD_names:
    t = table[["sequence_short", "codec_short", yname]].pivot_table(index="sequence_short", columns="codec_short")
    t.index.name = None
    t = t.T
    t = t.reset_index(level=0)
    t.index.name = None
    t = t.drop(columns="level_0")
    t = t.T
    t = t.drop(columns="x264")
    t.columns.name = "Sekvence"
    t.loc["Průměr"] = t.mean()
    column_format = "|l|" + "".join(["r|"]*len(t.columns))
    out = graphics_dir + yname + ".tex"
    with open(out, "w") as f:
        f.write(t.to_latex(
            column_format=column_format, formatters=[formatter1 for i in range(t.shape[1])], escape=False,
            ).replace('\\\\\n', '\\\\ \\hline\n').replace('\\\\ \\hline\n', '\\\\ \\hline\\hline\n', 1).replace('}\n', '}\n\\hline\n', 1))
        #.background_gradient(axis=None)
        #f.write(t.style.format(decimal=",", precision=2).to_latex(
            #column_format=column_format
            #).replace('\\\\\n', '\\\\ \\hline\n').replace('\\\\ \\hline\n', '\\\\ \\hline\\hline\n', 1).replace('}\n', '}\n\\hline\n', 1))



'''
bj_psnr = []
bj_psnr_rate = []

bj_ssim = []
bj_ssim_rate = []

bj_msssim = []
bj_msssim_rate = []

bj_vmaf = []
bj_vmaf_rate = []

for sequence in sequences:
    print(sequence)
    psnr_bitrates = []
    ssim_bitrates = []
    msssim_bitrates = []
    vmaf_bitrates = []
    psnr_cpu_times = []
    psnr_times = []
    time_bitrates = []
    decode_time_bitrates = []
    psnr_cpu_times_fps = []
    psnr_times_fps = []
    time_bitrates_fps = []
    decode_times_bitrates = []
    RSS = []
    codec_series = []
    for serie in data:
        try:
            series_label(serie.serie, sequence=sequence)
            psnr_bitrates.append(sorted(zip(serie.avg_bitrate_mb, serie.psnr_avg)))
            ssim_bitrates.append(sorted(zip(serie.avg_bitrate_mb, serie.ssim_avg)))
            msssim_bitrates.append(sorted(zip(serie.avg_bitrate_mb, serie.msssim_avg)))
            vmaf_bitrates.append(sorted(zip(serie.avg_bitrate_mb, serie.vmaf_avg)))
            psnr_cpu_times.append(sorted(zip(serie.cpu_time, serie.psnr_avg)))
            psnr_times.append(sorted(zip(serie.total_time, serie.psnr_avg)))
            psnr_cpu_times_fps.append(sorted(zip(serie.cpu_time_fps, serie.psnr_avg)))
            psnr_times_fps.append(sorted(zip(serie.total_time_fps, serie.psnr_avg)))
            RSS.append(sorted(zip(serie.max_RSS, serie.med_RSS, serie.perc_RSS)))
            time_bitrates.append(sorted(zip(serie.avg_bitrate_mb, serie.cpu_time)))
            time_bitrates_fps.append(sorted(zip(serie.avg_bitrate_mb, serie.cpu_time_fps)))
            decode_times_bitrates.append(sorted(zip(serie.avg_bitrate_mb, serie.decode_time_fps)))
            codec_series.append(serie.label)
        except KeyError:
            pass

    short_name = sequences_short[sequence]
    composite_plot_smooth(psnr_bitrates, codec_series, "Bitrate [Mbit/s]", "PSNR (YUV) [dB]", "graphs/" + short_name + "_psnr", xlim=bitrate_lim[sequence], ylim=psnr_lim[sequence])
    composite_plot_smooth(ssim_bitrates, codec_series, "Bitrate [Mbit/s]", "SSIM", "graphs/" + short_name + "_ssim", xlim=bitrate_lim[sequence], ylim=ssim_lim[sequence])
    composite_plot_smooth(msssim_bitrates, codec_series, "Bitrate [Mbit/s]", "MS-SSIM", "graphs/" + short_name + "_msssim", xlim=bitrate_lim[sequence], ylim=msssim_lim[sequence])
    composite_plot_smooth(vmaf_bitrates, codec_series, "Bitrate [Mbit/s]", "VMAF", "graphs/" + short_name + "_vmaf", xlim=bitrate_lim[sequence], ylim=vmaf_lim[sequence])
    composite_plot_smooth(psnr_cpu_times, codec_series, "Procesorový čas [s]", "PSNR (YUV) [dB]", "graphs/" + short_name + "_cpu_times", xlim=cpu_time_lim[sequence])
    composite_plot_smooth(psnr_times, codec_series, "Čas zpracování [s]", "PSNR (YUV) [dB]", "graphs/" + short_name + "_times", xlim=processing_lim[sequence])
    composite_plot_smooth(time_bitrates, codec_series, "Bitrate [Mbit/s]", "Procesorový čas [s]", "graphs/" + short_name + "_times_bitrate", xlim=bitrate_lim[sequence], ylim=cpu_time_lim[sequence])
    composite_plot_smooth(psnr_cpu_times_fps, codec_series, "Procesorový čas [s/frame]", "PSNR (YUV) [dB]", "graphs/" + short_name + "_cpu_times_fps", xlim=tuple([x/serie.frames for x in cpu_time_lim[sequence]]))
    composite_plot_smooth(psnr_times_fps, codec_series, "Čas zpracování [s/frame]", "PSNR (YUV) [dB]", "graphs/" + short_name + "_times_fps", xlim=tuple([x/serie.frames for x in processing_lim[sequence]]))
    composite_plot_smooth(time_bitrates_fps, codec_series, "Bitrate [Mbit/s]", "Procesorový čas [s/frame]", "graphs/" + short_name + "_times_fps_bitrate", xlim=bitrate_lim[sequence], ylim=tuple([x/serie.frames for x in cpu_time_lim[sequence]]))
    composite_plot_smooth(decode_times_bitrates, codec_series, "Bitrate [Mbit/s]", "Rychlost dekódování [frame/s]", "graphs/" + short_name + "_decode_perf", xlim=bitrate_lim[sequence])

    t1, t2 = calc_bj_cross_to_table(psnr_bitrates, [x.rsplit(" ")[0] for x in codec_series], "PSNR", "rate")
    bj_psnr.append(t1)
    bj_psnr_rate.append(t2)

    t1, t2 = calc_bj_cross_to_table(ssim_bitrates, [x.rsplit(" ")[0] for x in codec_series], "SSIM", "rate")
    bj_ssim.append(t1)
    bj_ssim_rate.append(t2)

    t1, t2 = calc_bj_cross_to_table(msssim_bitrates, [x.rsplit(" ")[0] for x in codec_series], "MS-SSIM", "rate")
    bj_msssim.append(t1)
    bj_msssim_rate.append(t2)

    t1, t2 = calc_bj_cross_to_table(vmaf_bitrates, [x.rsplit(" ")[0] for x in codec_series], "VMAF", "rate")
    bj_vmaf.append(t1)
    bj_vmaf_rate.append(t2)

    i = enc.count()
    for mem in RSS:
        t = zip(*mem)
        m, med, perc = [list(t) for t in t]
        l = codec_series[next(i)]
        print(f"%{l}: RSS (MiB): max: {np.array(m).max()/1024/1024} med: {np.array(med).mean()/1024/1024} 90.perc: {np.array(perc).mean()/1024/1024}")


print(f"{bcolors.BOLD}{bcolors.OKGREEN}PSNR{bcolors.ENDC}")
c = pd.concat(bj_psnr)
g = c.groupby(c.index)
print(g.mean().to_latex(float_format="%.2f"))
print("\caption{test}")

print(f"{bcolors.BOLD}{bcolors.OKGREEN}PSNR-rate{bcolors.ENDC}")
c = pd.concat(bj_psnr_rate)
g = c.groupby(c.index)
print(g.mean().to_latex(formatters=[f2 for i in range(g.mean().shape[1])], escape=False))


print(f"{bcolors.BOLD}{bcolors.OKGREEN}SSIM{bcolors.ENDC}")
c = pd.concat(bj_ssim)
g = c.groupby(c.index)
print(g.mean().to_latex(float_format="%.2f"))

print(f"{bcolors.BOLD}{bcolors.OKGREEN}SSIM-rate{bcolors.ENDC}")
c = pd.concat(bj_ssim_rate)
g = c.groupby(c.index)
print(g.mean().to_latex(formatters=[f2 for i in range(g.mean().shape[1])], escape=False))


print(f"{bcolors.BOLD}{bcolors.OKGREEN}MS-SSIM{bcolors.ENDC}")
c = pd.concat(bj_msssim)
g = c.groupby(c.index)
print(g.mean().to_latex(float_format="%.2f"))

print(f"{bcolors.BOLD}{bcolors.OKGREEN}MS-SSIM-rate{bcolors.ENDC}")
c = pd.concat(bj_msssim_rate)
g = c.groupby(c.index)
print(g.mean().to_latex(formatters=[f2 for i in range(g.mean().shape[1])], escape=False))


print(f"{bcolors.BOLD}{bcolors.OKGREEN}VMAF{bcolors.ENDC}")
c = pd.concat(bj_vmaf)
g = c.groupby(c.index)
print(g.mean().to_latex(float_format="%.2f"))

print(f"{bcolors.BOLD}{bcolors.OKGREEN}VMAF-rate{bcolors.ENDC}")
c = pd.concat(bj_vmaf_rate)
g = c.groupby(c.index)
print(g.mean().to_latex(formatters=[f2 for i in range(g.mean().shape[1])], escape=False))
'''
