from __future__ import absolute_import, division, print_function

import numpy as np

from isis_imaging import helper as h


def _cli_register(parser):
    parser.add_argument(
        "--clip-min",
        required=False,
        type=float,
        default=None,
        help="Clip values from the image BELOW the specified amount. "
        "If not passed the minimum value in the volume will be taken")

    parser.add_argument(
        "--clip-max",
        required=False,
        type=float,
        default=None,
        help="Clip values from the image ABOVE the specified amount. "
        "If not passed the minimum value in the volume will be taken")

    return parser


def _gui_register(main_window):
    from isis_imaging.core.algorithms import gui_compile_ui as gcu
    from gui.algorithm_dialog import AlgorithmDialog
    from PyQt5 import Qt
    dialog = AlgorithmDialog(main_window)
    gcu.execute("gui/ui/alg_dialog.ui", dialog)
    dialog.setWindowTitle("Clip Values")

    label_clip_min = QtGui.QLabel("Clip Min")
    label_clip_max = QtGui.QLabel("Clip Max")
    clip_min_field = QtGui.QDoubleSpinBox()
    clip_min_field.setDecimals(7)
    clip_min_field.setMinimum(-1000000)
    clip_max_field = QtGui.QDoubleSpinBox()
    clip_max_field.setDecimals(7)
    clip_max_field.setMaximum(1000000)

    dialog.formLayout.addRow(label_clip_min, clip_min_field)
    dialog.formLayout.addRow(label_clip_max, clip_max_field)

    def decorate_execute():
        clip_min = clip_min_field.value()
        clip_max = clip_max_field.value()
        from functools import partial
        return partial(execute, clip_min=clip_min, clip_max=clip_max)

    # replace dialog function with this one
    dialog.decorate_execute = decorate_execute
    return dialog


def execute(data, clip_min=None, clip_max=None):
    """
    Clip values below the min and above the max pixels.

    :param data: Input data as a 3D numpy.ndarray

    :param clip_min: The minimum value to be clipped from the data

    :param clip_max: The maximum value to be clipped from the data

    :return: The processed 3D numpy.ndarray

    Example command line:

    isis_imaging -i /some/data/ --clip-min -120 --clip-max 42
    """

    # we're using is not None because if the value specified is 0.0 that evaluates to false
    if clip_min is not None or clip_max is not None:
        clip_min = clip_min if clip_min is not None else data.min()
        clip_max = clip_max if clip_max is not None else data.max()
        h.pstart("Clipping data with values min {0} and max {1}.".format(
            clip_min, clip_max))

        np.clip(data, clip_min, clip_max, data)

        h.pstop("Finished data clipping.")

    return data
