from __future__ import absolute_import, division, print_function

import numpy as np

import helper as h


def cli_register(parser):
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


def gui_register(dialog):
    from core.algorithms import gui_compile_ui as gcu
    from PyQt4 import QtGui
    if dialog is None:
        dialog = QtGui.QDialog()
        gcu.execute("gui/ui/alg_dialog.ui", dialog)
        dialog.setWindowTitle("Clip Values")

    clip_min = QtGui.QLabel("Clip Min")
    clip_max = QtGui.QLabel("Clip Max")
    clip_min_field = QtGui.QDoubleSpinBox()
    clip_max_field = QtGui.QDoubleSpinBox()

    dialog.formLayout.addRow(clip_min, clip_min_field)
    dialog.formLayout.addRow(clip_max, clip_max_field)

    dialog.accepted.connect(lambda x: print("I hath been accepted"))

    return dialog


def execute(data, clip_min=None, clip_max=None):
    """
    Execute the Clip filter.
    Clip values below the min and above the max pixels.

    :param data: The sample image data as a 3D numpy.ndarray
    :param clip_min: The minimum value to be clipped
    :param clip_max: The maximum value to be clipped

    :return: the data after being processed with the filter

    Example command line:
    python main.py -i /some/data/ --clip-min -120 --clip-max 42
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
