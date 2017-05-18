from __future__ import (absolute_import, division, print_function)
import helper as h
import numpy as np


def cli_register(parser):
    parser.add_argument(
        "--cut-off",
        required=False,
        type=float,
        default=None,
        help="Cut off values above threshold relative to the max pixels. "
        "The threshold must be in range 0 < threshold < 1. "
        "Example: --cut-off 0.95")

    return parser


def gui_register(main_window):
    from core.algorithms import gui_compile_ui as gcu
    from gui.algorithm_dialog import AlgorithmDialog
    from PyQt4 import QtGui
    dialog = AlgorithmDialog(main_window)
    gcu.execute("gui/ui/alg_dialog.ui", dialog)
    dialog.setWindowTitle("Cut Off")

    label_radius = QtGui.QLabel("Threshold")
    radius_field = QtGui.QDoubleSpinBox()
    radius_field.setMinimum(0)
    radius_field.setMaximum(1)
    radius_field.setValue(0.95)

    dialog.formLayout.addRow(label_radius, radius_field)

    def decorate_execute():
        from functools import partial
        return partial(execute, threshold=radius_field.value())

    # replace dialog function with this one
    dialog.decorate_execute = decorate_execute
    return dialog


def execute(data, threshold):
    """
    Execute the Cut off filter.
    Cut off values above threshold relative to the max pixels.

    :param data: The sample image data as a 3D numpy.ndarray
    :param threshold: The threshold related to the minimum
                      pixel value that will be clipped

    :return: the data after being processed with the filter

    Example command line:
    python main.py -i /some/data/ --cut-off 0.95
    """

    if threshold and threshold > 0.0:
        h.pstart("Applying cut-off with level: {0}".format(threshold))
        dmin = np.amin(data)
        dmax = np.amax(data)
        rel_cut_off = dmin + threshold * (dmax - dmin)

        data = np.minimum(data, rel_cut_off)

        h.pstop("Finished cut-off step, with pixel data type: {0}.".format(
            data.dtype))

    return data
