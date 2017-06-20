from __future__ import absolute_import, division, print_function

import cupy as cp

from isis_imaging import helper as h

# The smallest and largest allowed pixel value
MINIMUM_PIXEL_VALUE = 1e-9
MAXIMUM_PIXEL_VALUE = 3


def _cli_register(parser):
    # this doesn't have anything to add,
    # the options are added in the funcitonal config,
    # which should be moved to here TODO
    return parser


def _gui_register(main_window):
    pass


def execute(data,
            flat=None,
            dark=None,
            clip_min=MINIMUM_PIXEL_VALUE,
            clip_max=MAXIMUM_PIXEL_VALUE,
            cores=None,
            chunksize=None):
    """
    Normalise by flat and dark images

    :param data: Sample data which is to be processed. Expected in radiograms
    :param flat: flat (open beam) image to use in normalization
    :param dark: dark image to use in normalization
    :param clip_min: After normalisation, clip any pixels under this value.
    :param clip_max: After normalisation, clip any pixels over this value.
    :param cores: The number of cores that will be used to process the data.
    :param chunksize: The number of chunks that each worker will receive.

    :returns: filtered data (stack of images)

    Example command line:
    python main.py -i /some/data -F /some/flat/images -D /some/dark/images
    python main.py -i /some/data --input-path-flat /some/flat/images 
                   --input-path-flat /some/dark/images
    """

    if flat is not None and dark is not None and isinstance(
            flat, cp.ndarray) and isinstance(dark, cp.ndarray):
        if 2 != flat.ndim or 2 != dark.ndim:
            raise ValueError(
                "Incorrect shape of the flat image ({0}) or dark image ({1}) \
                which should match the shape of the sample images ({2})"
                .format(flat.shape, dark.shape, data[0].shape))

    return _execute_par(data, flat, dark, clip_min, clip_max, cores,
                        chunksize)


def _execute_par(data,
                 flat=None,
                 dark=None,
                 clip_min=MINIMUM_PIXEL_VALUE,
                 clip_max=MAXIMUM_PIXEL_VALUE,
                 cores=None,
                 chunksize=None):
    """
    A benchmark justifying the current implementation, performed on 500x2048x2048 images

    #1 Separate runs
    Subtract (sequential with np.subtract(data, dark, out=data)) - 13s
    Divide (par) - 1.15s

    #2 Separate parallel runs
    Subtract (par) - 5.5s
    Divide (par) - 1.15s

    #3 Added subtract into _divide so that it is:
                np.true_divide(np.subtract(data, dark, out=data), norm_divide, out=data)
    Subtract then divide (par) - 55s
    """
    h.pstart("Starting PARALLEL normalization by flat/dark images.")

    norm_divide = cp.zeros((1, data.shape[1], data.shape[2]), data.dtype)
    # remove a dimension, I found this to be the easiest way to do it
    norm_divide = norm_divide.reshape(data.shape[1], data.shape[2])

    cp.subtract(flat, dark, out=norm_divide)

    # prevent divide-by-zero issues, and negative pixels make no sense
    norm_divide[norm_divide == 0] = MINIMUM_PIXEL_VALUE

    # subtract the dark from all images
    cp.subtract(data, dark, out=data)

    cp.divide(data, norm_divide, out=data)

    # After scaling back the values some images will have pixels
    # with big negative values -25626262 which throws off contrast adjustments.
    # This will crop those negative pixels out, and set them to nearly zero
    # The negative values will also get scaled back after this in
    # value_scaling which will increase their values futher!
    cp.clip(data, clip_min, clip_max, out=data)

    h.pstop("Finished PARALLEL normalization by flat/dark images.")

    return data
