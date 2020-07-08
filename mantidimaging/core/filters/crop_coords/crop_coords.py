from functools import partial
from typing import Dict, Any

import numpy as np

from mantidimaging import helper as h
from mantidimaging.core.data import Images
from mantidimaging.core.filters.base_filter import BaseFilter
from mantidimaging.core.parallel import utility as pu
from mantidimaging.core.utility.progress_reporting import Progress
from mantidimaging.core.utility.sensible_roi import SensibleROI
from mantidimaging.gui.windows.stack_visualiser.presenter import SVParameters


class CropCoordinatesFilter(BaseFilter):
    filter_name = "Crop Coordinates"

    @staticmethod
    def filter_func(data: Images, region_of_interest: SensibleROI = None, progress=None) -> Images:
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

        :return: The processed 3D numpy.ndarray
        """

        if region_of_interest is None:
            region_of_interest = [0, 0, 50, 50]

        h.check_data_stack(data)

        sample = data.data
        shape = (sample.shape[0],
                 region_of_interest.height,
                 region_of_interest.width)
        sample_name = data.memory_filename
        if sample_name is not None:
            data.free_memory()
        output = pu.create_array(shape, sample.dtype, sample_name)
        data.data = execute_single(sample, region_of_interest, progress, out=output)

        return data

    @staticmethod
    def register_gui(form, on_change, view):
        from mantidimaging.gui.utility import add_property_to_form

        add_property_to_form('Select ROI on stack visualiser.', 'label', form=form)

        return {}

    @staticmethod
    def sv_params() -> Dict[str, Any]:
        return {'region_of_interest': SVParameters.ROI}

    @staticmethod
    def execute_wrapper(*args) -> partial:
        return partial(CropCoordinatesFilter.filter_func)


def execute_single(data, roi, progress=None, out=None):
    progress = Progress.ensure_instance(progress, task_name='Crop Coords')

    if roi:
        progress.add_estimated_steps(1)

        with progress:
            assert all(isinstance(region, int) for
                       region in roi), \
                "The region of interest coordinates are not integers!"

            progress.update(msg="Cropping with coordinates: {0}.".format(roi))

            output = out[:] if out is not None else data[:]
            output[:] = data[:, roi.top:roi.bottom, roi.left:roi.right]
    return output
