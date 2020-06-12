from functools import partial

import numpy as np

from mantidimaging import helper as h
from mantidimaging.core.data import Images
from mantidimaging.core.filters.base_filter import BaseFilter
from mantidimaging.core.parallel import shared_mem as psm
from mantidimaging.core.parallel import utility as pu
from mantidimaging.core.utility.progress_reporting import Progress


class RotateFilter(BaseFilter):
    filter_name = "Rotate Stack"

    @staticmethod
    def filter_func(data: Images, rotation=None, flat=None, dark=None, cores=None, chunksize=None, progress=None):
        """
        Rotates a stack (sample, flat and dark images).

        This function only works with square images.

        If the picture is cropped first, the ROI coordinates have to be adjusted
        separately to be pointing at the NON ROTATED image!

        :param data: stack of sample images
        :param rotation: The rotation to be performed
        :param flat: flat images average
        :param dark: dark images average
        :param cores: cores for parallel execution
        :param chunksize: chunk for each worker

        :return: rotated images
        """
        h.check_data_stack(data)

        if rotation:
            # rot90 rotates counterclockwise; config.args.rotation rotates
            # clockwise
            clockwise_rotations = 4 - rotation

            if pu.multiprocessing_available():
                _execute_par(data.sample, clockwise_rotations, cores, chunksize)
            else:
                _execute_seq(data.sample, clockwise_rotations)

            if flat is not None:
                flat = _rotate_image(flat, clockwise_rotations)
            if dark is not None:
                dark = _rotate_image(dark, clockwise_rotations)

        h.check_data_stack(data)

        if flat is None and dark is None:
            return data
        else:
            return data, flat, dark

    @staticmethod
    def register_gui(form, on_change):
        from mantidimaging.gui.utility import add_property_to_form

        _, rotation_count = add_property_to_form('Number of rotations clockwise',
                                                 'int',
                                                 1, (1, 3),
                                                 form=form,
                                                 on_change=on_change)

        return {"rotation_count": rotation_count}

    @staticmethod
    def execute_wrapper(rotation_count=None):
        return partial(RotateFilter.filter_func, rotation=rotation_count.value())


def _rotate_image_inplace(data, rotation=None):
    data[:, :] = np.rot90(data[:, :], rotation)


def _rotate_image(data, rotation=None):
    return np.rot90(data[:, :], rotation)


def _execute_seq(data, rotation, progress=None):
    progress = Progress.ensure_instance(progress, task_name='Rotate Stack')

    with progress:
        progress.update(msg=f"Starting rotation step ({rotation * 90} degrees clockwise), "
                        f"data type: {data.dtype}...")

        img_count = data.shape[0]
        progress.add_estimated_steps(img_count)
        for idx in range(0, img_count):
            data[idx] = _rotate_image(data[idx], rotation)
            progress.update()

    return data


def _execute_par(data, rotation, cores=None, chunksize=None, progress=None):
    progress = Progress.ensure_instance(progress, task_name='Rotate Stack')

    with progress:
        progress.update(msg=f"Starting PARALLEL rotation step ({rotation * 90} degrees "
                        f"clockwise), data type: {data.dtype}...")

        f = psm.create_partial(_rotate_image_inplace, fwd_func=psm.inplace, rotation=rotation)

        data = psm.execute(data, f, cores=cores, chunksize=chunksize, name="Rotation")

    return data
