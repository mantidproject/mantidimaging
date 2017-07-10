from __future__ import absolute_import, division, print_function

import numpy as np
from matplotlib import pyplot
# from .mslice_plotting import pyplot

HISTOGRAM_BIN_SIZE = 256


def _setup_normal(current_image, ax):
    ax.hist(current_image.flatten(), bins=HISTOGRAM_BIN_SIZE)


def _setup_transparent(current_image, ax):
    histogram, bins = np.histogram(current_image.flatten(), bins=512)
    center = (bins[:-1] + bins[1:]) / 2
    ax.plot(center, histogram)


def add_new_figure():
    fig = pyplot.figure()
    ax = fig.add_subplot(111)
    return ax


def _show():
    pyplot.show()
    # redraw the plot, this shows an updated histogram
    pyplot.draw()


def show(current_image):
    _setup_normal(current_image, pyplot)
    _show()


def show_transparent(current_image):
    _setup_transparent(current_image, pyplot)
    _show()


def show_floating(current_image):
    ax = add_new_figure()
    _setup_normal(current_image, ax)
    _show()


def show_floating_transparent(current_image):
    ax = add_new_figure()
    _setup_transparent(current_image, ax)
