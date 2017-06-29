from __future__ import absolute_import, division, print_function

import numpy as np

from isis_imaging import helper as h
from isis_imaging.core.tools import importer

OUTLIERS_DARK = 'dark'
OUTLIERS_BRIGHT = 'bright'
_default_radius = 3
_default_mode = OUTLIERS_BRIGHT


def _cli_register(parser):
    parser.add_argument(
        "--outliers",
        required=False,
        type=float,
        help="Pixel difference above which to crop bright pixels.")

    parser.add_argument(
        "--outliers-radius",
        default=_default_radius,
        required=False,
        type=int,
        help="Default: %(default)s. "
        "Radius for the median filter to determine the outlier.")

    parser.add_argument(
        "--outliers-mode",
        default=_default_mode,
        required=False,
        type=str,
        help="Default: %(default)s. "
        "Crop bright or dark pixels.\n"
        "Cropping dark pixels is more expensive. "
        "It will invert the image before and after removing the outliers")

    return parser


def _gui_register(main_window):
    from isis_imaging.core.algorithms import gui_compile_ui as gcu
    from gui.algorithm_dialog import AlgorithmDialog
    from PyQt5 import Qt
    dialog = AlgorithmDialog(main_window)
    gcu.execute("gui/ui/alg_dialog.ui", dialog)
    dialog.setWindowTitle("Outliers")

    label_diff = QtGui.QLabel("Difference")
    diff_field = QtGui.QSpinBox()
    diff_field.setMinimum(-1000000)
    diff_field.setMaximum(1000000)
    diff_field.setValue(1)

    label_size = QtGui.QLabel("Size")
    size_field = QtGui.QSpinBox()
    size_field.setMinimum(0)
    size_field.setMaximum(1000)
    size_field.setValue(3)

    label_mode = QtGui.QLabel("Mode")
    mode_field = QtGui.QComboBox()
    mode_field.addItems(modes())

    dialog.formLayout.addRow(label_diff, diff_field)
    dialog.formLayout.addRow(label_size, size_field)
    dialog.formLayout.addRow(label_mode, mode_field)

    def decorate_execute():
        from functools import partial
        return partial(
            execute,
            diff=diff_field.value(),
            radius=size_field.value(),
            mode=mode_field.currentText())

    # replace dialog function with this one
    dialog.decorate_execute = decorate_execute
    return dialog


def modes():
    return [OUTLIERS_BRIGHT, OUTLIERS_DARK]


def execute(data, diff, radius=_default_radius, mode=_default_mode,
            cores=None):
    """
    Execute the Outliers filter. Requires tomopy to be available.

    :param data: Input data as a 3D numpy.ndarray

    :param diff: Pixel value difference above which to crop bright pixels

    :param radius: Which pixels will be clipped: dark, bright or both

    :param cores: The number of cores that will be used to process the data.


    :return: The processed 3D numpy.ndarray

    Example command line:

    isis_imaging -i /some/data --outliers 1

    isis_imaging -i /some/data --outliers 1 --outliers-radius 4
    """

    if diff and radius and diff > 0 and radius > 0:
        h.pstart("Applying outliers with threshold: {0} and radius {1}".format(
            diff, radius))

        # we flip the histogram horizontally,
        # this makes the darkest pixels the brightest
        if mode == OUTLIERS_DARK:
            np.negative(data, out=data)

        tomopy = importer.do_importing('tomopy')

        data = tomopy.misc.corr.remove_outlier(data, diff, radius, ncore=cores)

        # reverse the inversion
        if mode == OUTLIERS_DARK:
            np.negative(data, out=data)

        h.pstop("Finished outliers step, with pixel data type: {0}.".format(
            data.dtype))

    return data
