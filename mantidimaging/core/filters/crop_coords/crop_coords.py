from functools import partial
from typing import Dict, Any

from mantidimaging.gui.windows.stack_visualiser.presenter import SVParameters

from mantidimaging import helper as h
from mantidimaging.core.filters.base_filter import BaseFilter
from mantidimaging.core.utility.progress_reporting import Progress


class CropCoordinatesFilter(BaseFilter):
    filter_name = "Crop Coordinates"

    def _filter_func(self, data, region_of_interest=None, flat=None, dark=None, progress=None):
        """
        Execute the Crop Coordinates by Region of Interest filter.
        This does NOT do any checks if the Region of interest is out of bounds!

        If the region of interest is out of bounds, the crop will **FAIL** at
        runtime.

        If the region of interest is in bounds, but has overlapping coordinates
        the crop give back a 0 shape of the coordinates that were wrong.

        :param data: Input data as a 3D numpy.ndarray

        :param region_of_interest: Crop original images using these coordinates.
                                   The selection is a rectangle and expected order
                                   is - Left Top Right Bottom.

        :param flat: The average flat image to be cropped

        :param dark: The average dark image to be cropped

        :return: The processed 3D numpy.ndarray
        """

        h.check_data_stack(data)

        # execute only for sample, if no flat and dark images are provided
        if data is not None and (flat is None or dark is None):
            return execute_single(data, region_of_interest, progress), None, None
        else:  # crop all and return as tuple
            return execute_single(data, region_of_interest, progress), \
                   execute_single(flat, region_of_interest, progress), \
                   execute_single(dark, region_of_interest, progress)

    def register_gui(self, form, on_change):
        from mantidimaging.gui.utility import add_property_to_form

        add_property_to_form(
            'Select ROI on stack visualiser.', 'label', form=form)

        return {}

    @property
    def params(self) -> Dict[str, Any]:
        return {
            'region_of_interest': SVParameters.ROI
        }

    def execute_wrapper(self, **kwargs) -> partial:
        return partial(self._filter_func)


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


def execute_single(data, region_of_interest, progress=None):
    progress = Progress.ensure_instance(progress, task_name='Crop Coords')

    if region_of_interest:
        progress.add_estimated_steps(1)

        with progress:
            assert all(isinstance(region, int) for
                       region in region_of_interest), \
                "The region of interest coordinates are not integers!"

            progress.update(msg="Cropping with coordinates: {0}.".format(
                region_of_interest))

            left = region_of_interest[0]
            top = region_of_interest[1]
            right = region_of_interest[2]
            bottom = region_of_interest[3]

            if data.ndim == 2:
                data = data[top:bottom, left:right]
            elif data.ndim == 3:
                data = data[:, top:bottom, left:right]

    return data
