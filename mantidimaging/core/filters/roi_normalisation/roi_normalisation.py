from functools import partial
from logging import getLogger
from typing import Dict, Any

import numpy as np

from mantidimaging import helper as h
from mantidimaging.core.filters.base_filter import BaseFilter
from mantidimaging.core.parallel import two_shared_mem as ptsm
from mantidimaging.core.parallel import utility as pu
from mantidimaging.core.utility.progress_reporting import Progress
from mantidimaging.gui.utility import add_property_to_form
from mantidimaging.gui.windows.stack_visualiser import SVParameters


class RoiNormalisationFilter(BaseFilter):
    filter_name = "ROI Normalisation"

    def _filter_func(self, data, air_region=None, cores=None, chunksize=None, progress=None):
        """
        Normalise by beam intensity.

        This does NOT do any checks if the Air Region is out of bounds!
        If the Air Region is out of bounds, the crop will fail at runtime.
        If the Air Region is in bounds, but has overlapping coordinates
        the crop give back a 0 shape of the coordinates that were wrong.

        :param data: Sample data which is to be processed. Expected in radiograms

        :param air_region: The order is - Left Top Right Bottom. The air region
                           from which sums will be calculated and all images will
                           be normalised.

        :param cores: The number of cores that will be used to process the data.

        :param chunksize: The number of chunks that each worker will receive.

        :returns: Filtered data (stack of images)
        """
        h.check_data_stack(data)

        # just get data reference
        if air_region:
            # sanity check for the regions
            assert all(isinstance(region, int) for region in
                       air_region), "The air region coordinates are not integers!"
            if pu.multiprocessing_available():
                data = _execute_par(data, air_region, cores, chunksize, progress)
            else:
                data = _execute_seq(data, air_region, progress)

        h.check_data_stack(data)
        return data

    def register_gui(self, form, on_change):
        add_property_to_form("Select ROI on stack visualiser.", "label", form=form, on_change=on_change)
        return {}

    def execute_wrapper(self):
        return partial(self._filter_func)

    @property
    def params(self) -> Dict[str, Any]:
        return {"air_region": SVParameters.ROI}


def _cli_register(parser):
    parser.add_argument(
        "-A",
        "--air-region",
        required=False,
        nargs='*',
        type=str,
        help="Air region /region for normalisation. The selection is a "
             "rectangle and expected order is - Left Top Right Bottom.\n"
             "For best results the region selected should not be blocked by "
             "any object in the Tomography.\n"
             "Example: --air-region 150 234 23 22")

    return parser


def _calc_sum(data,
              air_sums,
              air_left=None,
              air_top=None,
              air_right=None,
              air_bottom=None):
    # here we can use ndarray.sum or ndarray.mean
    # ndarray.mean makes the values with a nice int16 range
    # (0-65535, BUT NOT int16 TYPE! They remain floats!)
    # while ndarray.sum makes them in a low range of 0-1.5.
    # There is no difference in the results
    return data[air_top:air_bottom, air_left:air_right].mean()


def _divide_by_air_sum(data=None, air_sums=None):
    data[:] = np.true_divide(data, air_sums)


def _execute_par(data, air_region, cores=None, chunksize=None, progress=None):
    progress = Progress.ensure_instance(progress,
                                        task_name='ROI Normalisation')
    log = getLogger(__name__)

    left = air_region[0]
    top = air_region[1]
    right = air_region[2]
    bottom = air_region[3]

    with progress:
        progress.update(msg="Normalization by air region")

        # initialise same number of air sums
        img_num = data.shape[0]
        air_sums = pu.create_shared_array((img_num, 1, 1))

        # turn into a 1D array, from the 3D that is returned
        air_sums = air_sums.reshape(img_num)

        calc_sums_partial = ptsm.create_partial(
            _calc_sum,
            fwd_function=ptsm.return_to_second,
            air_left=left,
            air_top=top,
            air_right=right,
            air_bottom=bottom)

        data, air_sums = ptsm.execute(data, air_sums, calc_sums_partial, cores,
                                      chunksize, "Calculating air sums")

        air_sums_partial = ptsm.create_partial(
            _divide_by_air_sum, fwd_function=ptsm.inplace)

        data, air_sums = ptsm.execute(data, air_sums, air_sums_partial, cores,
                                      chunksize, "Norm by Air Sums")

        avg = np.average(air_sums)
        max_avg = np.max(air_sums) / avg
        min_avg = np.min(air_sums) / avg

        log.info("Normalization by air region. "
                 "Average: {0}, max ratio: {1}, min ratio: {2}.".format(
            avg, max_avg, min_avg))

    return data


def _execute_seq(data, air_region, progress):
    progress = Progress.ensure_instance(progress,
                                        task_name='ROI Normalisation')
    log = getLogger(__name__)

    left = air_region[0]
    top = air_region[1]
    right = air_region[2]
    bottom = air_region[3]

    with progress:
        progress.update(msg="Normalization by air region")
        progress.add_estimated_steps((2 * data.shape[0]) + 1)

        air_sums = []
        for idx in range(0, data.shape[0]):
            air_data_sum = data[idx, top:bottom, left:right].sum()
            air_sums.append(air_data_sum)
            progress.update()

        progress.update(msg="Normalization by air sums")
        air_sums = np.true_divide(air_sums, np.amax(air_sums))
        for idx in range(0, data.shape[0]):
            data[idx, :, :] = np.true_divide(data[idx, :, :], air_sums[idx])
            progress.update()

        avg = np.average(air_sums)
        max_avg = np.max(air_sums) / avg
        min_avg = np.min(air_sums) / avg

        log.info("Normalization by air region. "
                 "Average: {0}, max ratio: {1}, min ratio: {2}.".format(
            avg, max_avg, min_avg))

    return data
