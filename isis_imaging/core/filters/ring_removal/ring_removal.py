from __future__ import (absolute_import, division, print_function)
from isis_imaging import helper as h
import tomopy.misc.corr


def _cli_register(parser):
    parser.add_argument(
        "--ring-removal",
        required=False,
        action='store_true',
        help='Perform Ring Removal on the post processed data.')

    parser.add_argument(
        "--ring-removal-x",
        type=int,
        required=False,
        help='Abscissa location of center of rotation')

    parser.add_argument(
        "--ring-removal-y",
        type=int,
        required=False,
        help='Ordinate location of center of rotation')

    parser.add_argument(
        "--ring-removal-thresh",
        type=float,
        required=False,
        help='Maximum value of an offset due to a ring artifact')

    parser.add_argument(
        "--ring-removal-thresh-max",
        type=float,
        required=False,
        help='Max value for portion of image to filter')

    parser.add_argument(
        "--ring-removal-thresh-min",
        type=float,
        required=False,
        help='Min value for portion of image to filter')

    parser.add_argument(
        "--ring-removal-theta-min",
        type=int,
        required=False,
        help='Minimum angle in degrees (int) to be considered ring artifact')

    parser.add_argument(
        "--ring-removal-rwidth",
        type=int,
        required=False,
        help='Maximum width of the rings to be filtered in pixels')
    return parser


def _gui_register(main_window):
    from isis_imaging.core.algorithms import gui_compile_ui as gcu
    from gui.algorithm_dialog import AlgorithmDialog
    from PyQt4 import QtGui
    dialog = AlgorithmDialog(main_window)
    gcu.execute("gui/ui/alg_dialog.ui", dialog)
    dialog.setWindowTitle("Ring Removal")

    label_x = QtGui.QLabel("Abcissa X")
    x_field = QtGui.QSpinBox()
    x_field.setMinimum(0)
    x_field.setMaximum(1000000)

    label_y = QtGui.QLabel("Ordinate Y")
    y_field = QtGui.QSpinBox()
    y_field.setMinimum(0)
    y_field.setMaximum(1000000)

    label_thresh = QtGui.QLabel("Threshold")
    thresh = QtGui.QDoubleSpinBox()
    thresh.setMinimum(-1000000)
    thresh.setMaximum(1000000)

    label_thresh_min = QtGui.QLabel("Threshold Min")
    thresh_min = QtGui.QDoubleSpinBox()
    thresh_min.setMinimum(-1000000)
    thresh_min.setMaximum(1000000)

    label_thresh_max = QtGui.QLabel("Threshold Max")
    thresh_max = QtGui.QDoubleSpinBox()
    thresh_max.setMinimum(-1000000)
    thresh_max.setMaximum(1000000)

    label_theta = QtGui.QLabel("Theta")
    theta = QtGui.QSpinBox()
    theta.setMinimum(-1000)
    theta.setMaximum(1000)

    label_rwidth = QtGui.QLabel("RWidth")
    rwidth = QtGui.QSpinBox()
    rwidth.setMinimum(-1000000)
    rwidth.setMaximum(1000000)

    dialog.formLayout.addRow(label_x, x_field)
    dialog.formLayout.addRow(label_y, y_field)
    dialog.formLayout.addRow(label_thresh, thresh)
    dialog.formLayout.addRow(label_thresh_min, thresh_min)
    dialog.formLayout.addRow(label_thresh_max, thresh_max)
    dialog.formLayout.addRow(label_theta, theta)
    dialog.formLayout.addRow(label_rwidth, rwidth)

    def decorate_execute():
        from functools import partial
        return partial(
            execute,
            center_x=x_field,
            center_y=y_field,
            thresh=thresh,
            thresh_max=thresh_max,
            thresh_min=thresh_min,
            theta_min=theta,
            rwidth=rwidth)

    # replace dialog function with this one
    dialog.decorate_execute = decorate_execute
    return dialog


def execute(data,
            run_ring_removal=False,
            center_x=None,
            center_y=None,
            thresh=300.0,
            thresh_max=300.0,
            thresh_min=-100.0,
            theta_min=30,
            rwidth=30,
            cores=None,
            chunksize=None):
    """
    Removal of ring artifacts in reconstructed volume.

    :param data: Sample data which is to be processed. Expected in radiograms
    :param run_ring_removal: Uses Wavelet-Fourier based ring removal
    :param center_x: (float, optional) abscissa location of center of rotation
    :param center_y: (float, optional) ordinate location of center of rotation
    :param thresh: (float, optional)
                   maximum value of an offset due to a ring artifact
    :param thresh_max: (float, optional)
                   max value for portion of image to filter
    :param thresh_min: (float, optional)
                   min value for portion of image to filer
    :param theta_min: (int, optional)
                      minimum angle in degrees to be considered ring artifact
    :param rwidth: (int, optional)
                   Maximum width of the rings to be filtered in pixels
    :returns: Filtered data
    """

    if run_ring_removal:
        h.check_data_stack(data)
        h.pstart("Starting ring removal...")
        data = tomopy.misc.corr.remove_ring(
            data,
            center_x=center_x,
            center_y=center_y,
            thresh=thresh,
            thresh_max=thresh_max,
            thresh_min=thresh_min,
            theta_min=theta_min,
            rwidth=rwidth,
            ncore=cores,
            nchunk=chunksize)
        h.pstop("Finished ring removal...")

    return data
