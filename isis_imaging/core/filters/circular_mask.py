from __future__ import (absolute_import, division, print_function)
import helper as h
from core.tools import importer


def cli_register(parser):
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


def gui_register(dialog):
    from core.algorithms import gui_compile_ui as gcu

    if dialog is None:
        dialog = gcu.execute("gui/ui/alg_dialog.ui")
    return dialog


def execute(data, circular_mask_ratio, circular_mask_value=0., cores=None):
    """
    Execute the Circular Mask filter.

    :param data: The sample image data as a 3D numpy.ndarray
    :param circular_mask_ratio: The ratio to the full image.
                                The ratio must be 0 < ratio < 1
    :param circular_mask_value: Default 0.
                                The value that all pixels in the mask
                                will be set to.

    :return: the data after being processed with the filter

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
