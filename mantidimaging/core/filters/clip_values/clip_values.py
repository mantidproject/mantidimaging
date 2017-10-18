from __future__ import absolute_import, division, print_function

from mantidimaging.core.utility.progress_reporting import Progress


def _cli_register(parser):
    parser.add_argument(
        "--clip-min",
        required=False,
        type=float,
        default=None,
        help="Clip values from the image BELOW the specified amount. "
        "If not passed the minimum value in the volume will be taken")

    parser.add_argument(
        "--clip-min-new-value",
        required=False,
        type=float,
        default=None,
        help="The clipped values from --clip-min will be set to this new "
        "value. If this is not set the clipped values will be set to the "
        "--clip-min value. This allows to make noise values very far "
        "outliers, which can then be hidden in visualisation.")

    parser.add_argument(
        "--clip-max",
        required=False,
        type=float,
        default=None,
        help="Clip values from the image ABOVE the specified amount. "
        "If not passed the minimum value in the volume will be taken.")

    parser.add_argument(
        "--clip-max-new-value",
        required=False,
        type=float,
        default=None,
        help="The clipped values from --clip-max will be set to this new "
        "value. If this is not set the clipped values will be set to the "
        "--clip-max value. This allows to make noise values very far "
        "outliers, which can then be hidden in visualisation.")

    return parser


def execute(data,
            clip_min=None,
            clip_max=None,
            clip_min_new_value=None,
            clip_max_new_value=None,
            progress=None):
    """
    Clip values below the min and above the max pixels.

    :param data: Input data as a 3D numpy.ndarray.

    :param clip_min: The minimum value to be clipped from the data.
                     If None is provided then no lower threshold is used.

    :param clip_max: The maximum value to be clipped from the data.
                     If None is provided then no upper threshold is used.

    :param clip_min_new_value: The value to use when replacing values less than
                               clip_min.
                               If None is provided then the value of clip_min
                               is used.

    :param clip_max_new_value: The value to use when replacing values greater
                               than clip_max.
                               If None is provided then the value of clip_max
                               is used.

    :return: The processed 3D numpy.ndarray.
    """
    progress = Progress.ensure_instance(progress, task_name='Clip Values')

    # we're using is not None because if the value specified is 0.0 that
    # evaluates to false
    if clip_min is not None or clip_max is not None:
        with progress:
            clip_min = clip_min if clip_min is not None else data.min()
            clip_max = clip_max if clip_max is not None else data.max()

            clip_min_new_value = clip_min_new_value \
                if clip_min_new_value is not None else clip_min

            clip_max_new_value = clip_max_new_value \
                if clip_max_new_value is not None else clip_max

            progress.update(msg="Clipping data with values min {0} and max "
                                "{1}.".format(clip_min, clip_max))

            # this is the fastest way to clip the values, np.clip does not do
            # the clipping in place and ends up copying the data
            data[data < clip_min] = clip_min_new_value
            data[data > clip_max] = clip_max_new_value

    return data
