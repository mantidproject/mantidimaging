from __future__ import (absolute_import, division, print_function)

import tomopy.misc.corr

from mantidimaging import helper as h
from mantidimaging.core.utility.progress_reporting import Progress


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
            chunksize=None,
            progress=None):
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
    progress = Progress.ensure_instance(progress,
                                        task_name='Ring Removal')

    if run_ring_removal:
        h.check_data_stack(data)

        with progress:
            progress.update(msg="Ring Removal")
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

    return data
