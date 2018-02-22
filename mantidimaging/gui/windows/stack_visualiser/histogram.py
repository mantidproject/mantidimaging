import numpy as np
from matplotlib import pyplot

HISTOGRAM_BIN_SIZE = 2048


def _setup_normal(current_image, ax, legend, title):
    ax.hist(current_image.flatten(), bins=HISTOGRAM_BIN_SIZE, label=legend)
    ax.legend(loc='upper left')
    ax.title(title)


def _setup_transparent(current_image, ax, legend):
    histogram, bins = np.histogram(
            current_image.flatten(), bins=HISTOGRAM_BIN_SIZE)
    center = (bins[:-1] + bins[1:]) / 2
    ax.plot(center, histogram, label=legend)
    ax.legend(loc='upper left')


def add_new_figure():
    fig = pyplot.figure()
    ax = fig.add_subplot(111)
    return ax


def _show():
    pyplot.show()
    # redraw the plot, this will show any new histograms
    pyplot.draw()


def show(current_image, legend, title):
    _setup_normal(current_image, pyplot, legend, title)
    pyplot.title(title)
    _show()
    return pyplot


def show_transparent(current_image, legend, title):
    _setup_transparent(current_image, pyplot, legend)
    pyplot.title(title)
    _show()
    return pyplot


def show_floating(current_image, legend, title):
    ax = add_new_figure()
    _setup_normal(current_image, ax, legend, title)
    ax.set_title(title)
    _show()
    return ax


def show_floating_transparent(current_image, legend, title):
    ax = add_new_figure()
    _setup_transparent(current_image, ax, legend)
    ax.set_title(title)
    _show()
    return ax
