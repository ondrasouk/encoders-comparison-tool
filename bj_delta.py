import numpy as np
import numpy.typing as npt
from typing import Optional
import scipy
# BD-Rate and BD-PNSR computation
# (c) Joao Ascenso (joao.ascenso@lx.it.pt)
# Original work source: https://github.com/jascenso/bjontegaard_metrics
# edited by Ondrej Soukenik
# Added:
# Enhanced version of BD-Rate and BD-PSNR with Akima interpolation (function
# bj_delta_akima)


def bj_delta(R1: npt.ArrayLike, PSNR1: npt.ArrayLike, R2: npt.ArrayLike, PSNR2: npt.ArrayLike, mode: int = 0,
             anchors: Optional[tuple[float, float]] = None) -> float:
    lR1 = np.log(R1)
    lR2 = np.log(R2)

    # find integral
    if mode == 0:
        # least squares polynomial fit
        p1 = np.polyfit(lR1, PSNR1, 3)
        p2 = np.polyfit(lR2, PSNR2, 3)

        # integration interval
        if anchors is None:
            min_int = max(min(lR1), min(lR2))
            max_int = min(max(lR1), max(lR2))
        else:
            min_int = anchors[0]
            max_int = anchors[1]

        # indefinite integral of both polynomial curves
        p_int1 = np.polyint(p1)
        p_int2 = np.polyint(p2)

        # evaluates both poly curves at the limits of the integration interval
        # to find the area
        int1 = np.polyval(p_int1, max_int) - np.polyval(p_int1, min_int)
        int2 = np.polyval(p_int2, max_int) - np.polyval(p_int2, min_int)

        # find avg diff between the areas to obtain the final measure
        avg_diff = (int2-int1)/(max_int-min_int)
    else:
        # rate method: sames as previous one but with inverse order
        p1 = np.polyfit(PSNR1, lR1, 3)
        p2 = np.polyfit(PSNR2, lR2, 3)

        # integration interval
        if anchors is None:
            min_int = max(min(PSNR1), min(PSNR2))
            max_int = min(max(PSNR1), max(PSNR2))
        else:
            min_int = anchors[0]
            max_int = anchors[1]

        # indefinite interval of both polynomial curves
        p_int1 = np.polyint(p1)
        p_int2 = np.polyint(p2)

        # evaluates both poly curves at the limits of the integration interval
        # to find the area
        int1 = np.polyval(p_int1, max_int) - np.polyval(p_int1, min_int)
        int2 = np.polyval(p_int2, max_int) - np.polyval(p_int2, min_int)

        # find avg diff between the areas to obtain the final measure
        avg_exp_diff = (int2-int1)/(max_int-min_int)
        avg_diff = (np.exp(avg_exp_diff)-1)*100  # in percent
    return avg_diff


def bj_delta_akima(R1: npt.ArrayLike, PSNR1: npt.ArrayLike, R2: npt.ArrayLike, PSNR2: npt.ArrayLike, mode: int = 0,
                   anchors: Optional[tuple[float, float]] = None) -> float:
    lR1 = np.log(R1)
    lR2 = np.log(R2)

    # find integral
    if mode == 0:
        # Akima interpolation
        p1 = scipy.interpolate.Akima1DInterpolator(lR1, PSNR1)
        p2 = scipy.interpolate.Akima1DInterpolator(lR2, PSNR2)

        # integration interval
        if anchors is None:
            min_int = max(min(lR1), min(lR2))
            max_int = min(max(lR1), max(lR2))
        else:
            min_int = anchors[0]
            max_int = anchors[1]

        # evaluates both poly curves at the limits of the integration interval
        # to find the area
        int1 = scipy.integrate.quad(lambda x: p1(x), min_int, max_int)[0]
        int2 = scipy.integrate.quad(lambda x: p2(x), min_int, max_int)[0]

        # find avg diff between the areas to obtain the final measure
        avg_diff = (int2-int1)/(max_int-min_int)
    else:
        # rate method: sames as previous one but with inverse order
        p1 = scipy.interpolate.Akima1DInterpolator(PSNR1, lR1)
        p2 = scipy.interpolate.Akima1DInterpolator(PSNR2, lR2)

        # integration interval
        if anchors is None:
            min_int = max(min(PSNR1), min(PSNR2))
            max_int = min(max(PSNR1), max(PSNR2))
        else:
            min_int = anchors[0]
            max_int = anchors[1]

        # evaluates both poly curves at the limits of the integration interval
        # to find the area
        int1 = scipy.integrate.quad(lambda x: p1(x), min_int, max_int)[0]
        int2 = scipy.integrate.quad(lambda x: p2(x), min_int, max_int)[0]

        # find avg diff between the areas to obtain the final measure
        avg_exp_diff = (int2-int1)/(max_int-min_int)
        avg_diff = (np.exp(avg_exp_diff)-1)*100  # in percent
    return avg_diff
