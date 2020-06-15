from functools import partial
from typing import Dict, Any

from mantidimaging import helper as h
from mantidimaging.core.data import Images
from mantidimaging.core.filters.base_filter import BaseFilter
from mantidimaging.core.parallel import utility as pu
from mantidimaging.core.utility.progress_reporting import Progress
from mantidimaging.gui.windows.stack_visualiser.presenter import SVParameters


class CropCoordinatesFilter(BaseFilter):
    filter_name = "Crop Coordinates"

    @staticmethod
    def filter_func(data: Images, roi=None, progress=None) -> Images:
        """
        Execute the Crop Coordinates by Region of Interest filter.
        This does NOT do any checks if the Region of interest is out of bounds!

        If the region of interest is out of bounds, the crop will **FAIL** at
        runtime.

        If the region of interest is in bounds, but has overlapping coordinates
        the crop give back a 0 shape of the coordinates that were wrong.

        :param data: Input data as a 3D numpy.ndarray

        :param roi: Crop original images using these coordinates.
                                   The selection is a rectangle and expected order
                                   is - Left Top Right Bottom.

        :return: The processed 3D numpy.ndarray
        """

        if roi is None:
            roi = [0, 0, 50, 50]

        h.check_data_stack(data)

        sample = data.sample
        sample_name = data.sample_memory_file_name
        shape = (sample.shape[0], roi[2] - roi[0], roi[3] - roi[1])
        data.free_sample()
        output = pu.create_shared_array(sample_name, shape, sample.dtype)
        data.sample = execute_single(sample, roi, progress, out=output)

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

            left = roi[0]
            top = roi[1]
            right = roi[2]
            bottom = roi[3]

            output = out if out is not None else data
            if data.ndim == 2:
                output = data[top:bottom, left:right]
            elif data.ndim == 3:
                output = data[:, top:bottom, left:right]
    return output
