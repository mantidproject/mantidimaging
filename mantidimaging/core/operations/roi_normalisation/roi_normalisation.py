# Copyright (C) 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later

from functools import partial
from logging import getLogger

import numpy as np

from mantidimaging import helper as h
from mantidimaging.core.data import Images
from mantidimaging.core.operations.base_filter import BaseFilter, FilterGroup
from mantidimaging.core.operations.rescale.rescale import RescaleFilter
from mantidimaging.core.parallel import shared as ps
from mantidimaging.core.parallel import utility as pu
from mantidimaging.core.utility import value_scaling
from mantidimaging.core.utility.progress_reporting import Progress
from mantidimaging.core.utility.sensible_roi import SensibleROI
from mantidimaging.gui.utility import add_property_to_form
from mantidimaging.gui.utility.qt_helpers import Type


class RoiNormalisationFilter(BaseFilter):
    """Normalises the image data by the average values in a region of interest.

    Intended to be used on: Projections

    When: Always, to ensure that any fluctuations in beam intensity are normalised.

    Caution: If you see horizontal lines in the sinogram this means some projections
    are brighter/darker than the rest. This can be fixed with this operation.
    """
    filter_name = "ROI Normalisation"

    @staticmethod
    def filter_func(images: Images, region_of_interest: SensibleROI = None, cores=None, chunksize=None, progress=None):
        """Normalise by beam intensity.

        This does NOT do any checks if the Air Region is out of bounds!
        If the Air Region is out of bounds, the crop will fail at runtime.
        If the Air Region is in bounds, but has overlapping coordinates
        the crop give back a 0 shape of the coordinates that were wrong.

        :param images: Sample data which is to be processed. Expected in radiograms

        :param region_of_interest: The order is - Left Top Right Bottom. The air region
                           from which sums will be calculated and all images will
                           be normalised.

        :param cores: The number of cores that will be used to process the data.

        :param chunksize: The number of chunks that each worker will receive.
        :param progress: Reference to a progress bar object

        :returns: Filtered data (stack of images)
        """
        h.check_data_stack(images)

        # just get data reference
        if region_of_interest:
            initial_image_max = images.data.max()

            progress = Progress.ensure_instance(progress, task_name='ROI Normalisation')
            _execute(images.data, region_of_interest, cores, chunksize, progress)
            progress.update(1, "Rescaling to input value range")
            images = RescaleFilter.filter_func(images,
                                               min_input=images.data.min(),
                                               max_input=images.data.max(),
                                               max_output=initial_image_max,
                                               progress=progress)
        h.check_data_stack(images)
        return images

    @staticmethod
    def register_gui(form, on_change, view):
        label, roi_field = add_property_to_form("ROI",
                                                Type.STR,
                                                form=form,
                                                on_change=on_change,
                                                default_value="0, 0, 200, 200")
        add_property_to_form("Select ROI",
                             "button",
                             form=form,
                             on_change=on_change,
                             run_on_press=lambda: view.roi_visualiser(roi_field))
        return {'roi_field': roi_field}

    @staticmethod
    def execute_wrapper(roi_field):
        try:
            roi = SensibleROI.from_list([int(number) for number in roi_field.text().strip("[").strip("]").split(",")])
            return partial(RoiNormalisationFilter.filter_func, region_of_interest=roi)
        except Exception as e:
            raise ValueError(f"The provided ROI string is invalid! Error: {e}")

    @staticmethod
    def do_before_wrapper() -> partial:
        return partial(value_scaling.create_factors)

    @staticmethod
    def do_after_wrapper() -> partial:
        return partial(value_scaling.apply_factor)

    @staticmethod
    def group_name() -> FilterGroup:
        return FilterGroup.Basic


def _calc_sum(data, _, air_left=None, air_top=None, air_right=None, air_bottom=None):
    return data[air_top:air_bottom, air_left:air_right].mean()


def _divide_by_air_sum(data=None, air_sums=None):
    data[:] = np.true_divide(data, air_sums)


def _execute(data: np.ndarray, air_region: SensibleROI, cores=None, chunksize=None, progress=None):
    log = getLogger(__name__)

    with progress:
        progress.update(msg="Normalization by air region")
        if isinstance(air_region, list):
            air_region = SensibleROI.from_list(air_region)

        # initialise same number of air sums
        img_num = data.shape[0]
        air_sums = pu.create_array((img_num, ), data.dtype)

        do_calculate_air_sums = ps.create_partial(_calc_sum,
                                                  fwd_function=ps.return_to_second,
                                                  air_left=air_region.left,
                                                  air_top=air_region.top,
                                                  air_right=air_region.right,
                                                  air_bottom=air_region.bottom)

        ps.shared_list = [data, air_sums]
        ps.execute(do_calculate_air_sums, data.shape[0], progress, cores=cores)

        do_divide = ps.create_partial(_divide_by_air_sum, fwd_function=ps.inplace2)
        ps.execute(do_divide, data.shape[0], progress, cores=cores)

        avg = np.average(air_sums)
        max_avg = np.max(air_sums) / avg
        min_avg = np.min(air_sums) / avg

        log.info(f"Normalization by air region. " f"Average: {avg}, max ratio: {max_avg}, min ratio: {min_avg}.")
