from functools import partial
from logging import getLogger
from typing import Dict, Any

import numpy as np

from mantidimaging import helper as h
from mantidimaging.core.data import Images
from mantidimaging.core.filters.base_filter import BaseFilter
from mantidimaging.core.filters.rescale import RescaleFilter
from mantidimaging.core.parallel import two_shared_mem as ptsm
from mantidimaging.core.parallel import utility as pu
from mantidimaging.core.utility import value_scaling
from mantidimaging.core.utility.progress_reporting import Progress
from mantidimaging.core.utility.sensible_roi import SensibleROI
from mantidimaging.gui.utility import add_property_to_form
from mantidimaging.gui.windows.stack_visualiser import SVParameters


class RoiNormalisationFilter(BaseFilter):
    filter_name = "ROI Normalisation"

    @staticmethod
    def filter_func(images: Images, air_region: SensibleROI = None, cores=None, chunksize=None, progress=None):
        """
        Normalise by beam intensity.

        This does NOT do any checks if the Air Region is out of bounds!
        If the Air Region is out of bounds, the crop will fail at runtime.
        If the Air Region is in bounds, but has overlapping coordinates
        the crop give back a 0 shape of the coordinates that were wrong.

        :param images: Sample data which is to be processed. Expected in radiograms

        :param air_region: The order is - Left Top Right Bottom. The air region
                           from which sums will be calculated and all images will
                           be normalised.

        :param cores: The number of cores that will be used to process the data.

        :param chunksize: The number of chunks that each worker will receive.
        :param progress: Reference to a progress bar object

        :returns: Filtered data (stack of images)
        """
        h.check_data_stack(images)

        # just get data reference
        if air_region:
            # rescale to 16-bit range before normalising the values
            images = RescaleFilter.filter_func(images, 0.0, 65535.0)
            if pu.multiprocessing_necessary(images.data.shape, cores):
                _execute_par(images.data, air_region, cores, chunksize, progress)
            else:
                _execute_seq(images.data, air_region, progress)

        h.check_data_stack(images)
        return images

    @staticmethod
    def register_gui(form, on_change, view):
        add_property_to_form("Select ROI on stack visualiser.", "label", form=form, on_change=on_change)
        return {}

    @staticmethod
    def execute_wrapper():
        return partial(RoiNormalisationFilter.filter_func)

    @staticmethod
    def do_before_wrapper() -> partial:
        return partial(value_scaling.create_factors)

    @staticmethod
    def do_after_wrapper() -> partial:
        return partial(value_scaling.apply_factor)

    @staticmethod
    def sv_params() -> Dict[str, Any]:
        return {"air_region": SVParameters.ROI}


def _calc_sum(data, air_sums, air_left=None, air_top=None, air_right=None, air_bottom=None):
    return data[air_top:air_bottom, air_left:air_right].mean()


def _divide_by_air_sum(data=None, air_sums=None):
    data[:] = np.true_divide(data, air_sums)


def _execute_par(data, air_region: SensibleROI, cores=None, chunksize=None, progress=None):
    progress = Progress.ensure_instance(progress, task_name='ROI Normalisation')
    log = getLogger(__name__)

    with progress:
        progress.update(msg="Normalization by air region")

        # initialise same number of air sums
        img_num = data.shape[0]
        with pu.temp_shared_array((img_num, 1, 1), data.dtype) as air_sums:
            # turn into a 1D array, from the 3D that is returned
            air_sums = air_sums.reshape(img_num)

            calc_sums_partial = ptsm.create_partial(_calc_sum,
                                                    fwd_function=ptsm.return_to_second,
                                                    air_left=air_region.left,
                                                    air_top=air_region.top,
                                                    air_right=air_region.right,
                                                    air_bottom=air_region.bottom)

            data, air_sums = ptsm.execute(data,
                                          air_sums,
                                          calc_sums_partial,
                                          cores,
                                          chunksize,
                                          "Calculating air sums",
                                          progress=progress)

            air_sums_partial = ptsm.create_partial(_divide_by_air_sum, fwd_function=ptsm.inplace)

            data, air_sums = ptsm.execute(data,
                                          air_sums,
                                          air_sums_partial,
                                          cores,
                                          chunksize,
                                          "Norm by Air Sums",
                                          progress=progress)

            avg = np.average(air_sums)
            max_avg = np.max(air_sums) / avg
            min_avg = np.min(air_sums) / avg

            log.info(f"Normalization by air region. " f"Average: {avg}, max ratio: {max_avg}, min ratio: {min_avg}.")


def _execute_seq(data, air_region: SensibleROI, progress):
    progress = Progress.ensure_instance(progress, task_name='ROI Normalisation')
    log = getLogger(__name__)

    with progress:
        progress.update(msg="Normalization by air region")
        progress.add_estimated_steps((2 * data.shape[0]) + 1)

        air_sums = []
        for idx in range(0, data.shape[0]):
            air_data_sum = data[idx, air_region.top:air_region.bottom, air_region.left:air_region.right].sum()
            air_sums.append(air_data_sum)
            progress.update()

        progress.update(msg="Normalization by air sums")
        air_sums = np.true_divide(air_sums, np.amax(air_sums))
        for idx in range(data.shape[0]):
            np.true_divide(data[idx], air_sums[idx], out=data[idx])
            progress.update()

        avg = np.average(air_sums)
        max_avg = np.max(air_sums) / avg
        min_avg = np.min(air_sums) / avg

        log.info(f"Normalization by air region. " f"Average: {avg}, max ratio: {max_avg}, min ratio: {min_avg}.")
