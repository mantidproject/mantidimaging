from __future__ import (absolute_import, division, print_function)
from isis_imaging import helper as h
from isis_imaging.core.tools import importer

__all__ = ['execute', '_gui_register', '_cli_register']


def _cli_register(parser):
    parser.add_argument(
        "--circular-mask",
        required=False,
        type=float,
        default=None,
        help="Radius of the circular mask to apply on the "
        "reconstructed volume.\n"
        "It is given in range [0,1) relative to the size of the "
        "smaller dimension/edge "
        "of the slices.\nEmpty or zero implies no masking.")

    parser.add_argument(
        "--circular-mask-val",
        required=False,
        type=float,
        default=0.0,
        help="Default: %(default)s. "
        "The value that the pixels in the mask will be set to.")

    return parser


def _gui_register(main_window):
    from isis_imaging.core.algorithms import gui_compile_ui as gcu
    from gui.algorithm_dialog import AlgorithmDialog
    from PyQt5 import Qt
    dialog = AlgorithmDialog(main_window)
    gcu.execute("gui/ui/alg_dialog.ui", dialog)
    dialog.setWindowTitle("Circular Mask")

    label_radius = QtGui.QLabel("Radius")
    radius_field = QtGui.QDoubleSpinBox()
    radius_field.setMinimum(0)
    radius_field.setMaximum(1)
    radius_field.setValue(0.95)

    label_value = QtGui.QLabel("Set to value")
    value_field = QtGui.QDoubleSpinBox()
    value_field.setMinimum(-100000)
    value_field.setMaximum(100000)
    value_field.setValue(0)

    dialog.formLayout.addRow(label_radius, radius_field)
    dialog.formLayout.addRow(label_value, value_field)

    def decorate_execute():
        from functools import partial
        return partial(
            execute,
            circular_mask_ratio=radius_field.value(),
            circular_mask_value=value_field.value())

    # replace dialog function with this one
    dialog.decorate_execute = decorate_execute
    return dialog


def execute(data, circular_mask_ratio, circular_mask_value=0., cores=None):
    """
    Execute the Circular Mask filter.

    :param data: Input data as a 3D numpy.ndarray

    :param circular_mask_ratio: The ratio to the full image.
                                The ratio must be 0 < ratio < 1

    :param circular_mask_value: Default 0.
                                The value that all pixels in the mask
                                will be set to.

    :return: The processed 3D numpy.ndarray

    Full Reference:
    http://tomopy.readthedocs.io/en/latest/api/tomopy.misc.corr.html?highlight=circular%20mask
    """

    if circular_mask_ratio and 0 < circular_mask_ratio < 1:
        tomopy = importer.do_importing('tomopy')
        h.pstart("Starting circular mask...")
        # for some reason this doesn't like the ncore param,
        # even though it's in the official tomopy docs
        tomopy.circ_mask(
            arr=data,
            axis=0,
            ratio=circular_mask_ratio,
            val=circular_mask_value)
        h.pstop("Finished applying circular mask.")

    return data
