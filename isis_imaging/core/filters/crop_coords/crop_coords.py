from __future__ import (absolute_import, division, print_function)
from isis_imaging import helper as h


def _cli_register(parser):
    parser.add_argument(
        "-R",
        "--region-of-interest",
        nargs='*',
        required=False,
        type=str,
        help="Crop original images using these coordinates. The selection is a"
        " rectangle and expected order is - Left Top Right Bottom.\n"
        "If not given, the whole images are used.\n"
        "Example: --region-of-interest 150 234 23 22.")

    return parser


def execute(data, region_of_interest, flat=None, dark=None):
    """
    Execute the Crop Coordinates by Region of Interest filter.
    This does NOT do any checks if the Region of interest is out of bounds!

    If the region of interest is out of bounds, the crop will **FAIL** at runtime.

    If the region of interest is in bounds, but has overlapping coordinates
    the crop give back a 0 shape of the coordinates that were wrong.

    :param data: Input data as a 3D numpy.ndarray

    :param region_of_interest: Crop original images using these coordinates.
                               The selection is a rectangle and expected order
                               is - Left Top Right Bottom.

    :param flat: The average flat image to be cropped

    :param dark: The average dark image to be cropped

    :return: The processed 3D numpy.ndarray

    Example command line:

    isis_imaging -i /some/data -R 134 203 170 250

    isis_imaging -i /some/data --region-of-interest 134 203 170 250
    """

    h.check_data_stack(data)

    # execute only for sample, if no flat and dark images are provided
    if data is not None and (flat is None or dark is None):
        return _execute(data, region_of_interest), None, None
    else:  # crop all and return as tuple
        return _execute(data, region_of_interest), \
            _execute(flat, region_of_interest), \
            _execute(dark, region_of_interest)


def _execute(data, region_of_interest):
    if region_of_interest:
        assert all(isinstance(region, int) for region in region_of_interest), \
            "The region of interest coordinates are not integers!"

        h.pstart("Starting cropping with coordinates: {0}. ...".format(
            region_of_interest))

        left = region_of_interest[0]
        top = region_of_interest[1]
        right = region_of_interest[2]
        bottom = region_of_interest[3]

        if data.ndim == 2:
            data = data[top:bottom, left:right]
        elif data.ndim == 3:
            data = data[:, top:bottom, left:right]

        h.pstop("Finished image cropping with pixel data type: {0}, "
                "resulting shape: {1}.".format(data.dtype, data.shape))

    return data
