from __future__ import (absolute_import, division, print_function)
from mantidimaging import helper as h
from mantidimaging.core.tools import importer

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


def execute(data, circular_mask_ratio, circular_mask_value=0., cores=None):
    """
    :param data: Input data as a 3D numpy.ndarray

    :param circular_mask_ratio: The ratio to the full image.
                                The ratio must be 0 < ratio < 1

    :param circular_mask_value: The value that all pixels in the mask
                                will be set to.

    :return: The processed 3D numpy.ndarray
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
