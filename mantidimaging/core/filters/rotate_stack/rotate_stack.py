from functools import partial

from skimage.transform import rotate

from mantidimaging import helper as h
from mantidimaging.core.data import Images
from mantidimaging.core.filters.base_filter import BaseFilter
from mantidimaging.core.parallel import shared_mem as psm
from mantidimaging.core.parallel import utility as pu
from mantidimaging.core.utility.progress_reporting import Progress
from mantidimaging.gui.utility.qt_helpers import Type


class RotateFilter(BaseFilter):
    filter_name = "Rotate Stack"

    @staticmethod
    def filter_func(data: Images, angle=None, flat=None, dark=None, cores=None, chunksize=None, progress=None):
        """
        Rotates a stack (sample, flat and dark images).

        This function only works with square images.

        If the picture is cropped first, the ROI coordinates have to be adjusted
        separately to be pointing at the NON ROTATED image!

        :param data: stack of sample images
        :param angle: The rotation to be performed, in degrees
        :param flat: flat images average
        :param dark: dark images average
        :param cores: cores for parallel execution
        :param chunksize: chunk for each worker

        :return: rotated images
        """
        h.check_data_stack(data)

        if angle:
            if pu.multiprocessing_necessary(data.sample.shape, cores):
                _execute_par(data.sample, angle, cores, chunksize, progress)
            else:
                _execute_seq(data.sample, angle, progress)

            if flat is not None:
                flat = _rotate_image(flat, angle)
            if dark is not None:
                dark = _rotate_image(dark, angle)

        h.check_data_stack(data)

        if flat is None and dark is None:
            return data
        else:
            return data, flat, dark

    @staticmethod
    def register_gui(form, on_change, view):
        from mantidimaging.gui.utility import add_property_to_form

        _, angle = add_property_to_form('Angle of rotation counter clockwise (degrees)',
                                        Type.FLOAT,
                                        0, (-180, 180),
                                        form=form,
                                        on_change=on_change)

        return {"angle": angle}

    @staticmethod
    def execute_wrapper(angle=None):
        return partial(RotateFilter.filter_func, angle=angle.value())


def _rotate_image_inplace(data, angle=None):
    data[:, :] = rotate(data[:, :], angle)


def _rotate_image(data, angle=None):
    return rotate(data[:, :], angle)


def _execute_seq(data, angle: float, progress: Progress):
    progress = Progress.ensure_instance(progress, num_steps=data.shape[0], task_name='Rotate Stack')

    with progress:
        img_count = data.shape[0]
        progress.add_estimated_steps(img_count)
        for idx in range(0, img_count):
            data[idx] = _rotate_image(data[idx], angle)
            progress.update(1, f"Rotating by {angle}")

    return data


def _execute_par(data, angle: float, cores: int, chunksize: int, progress: Progress):
    progress = Progress.ensure_instance(progress, task_name='Rotate Stack')

    with progress:
        f = psm.create_partial(_rotate_image_inplace, fwd_func=psm.inplace, angle=angle)

        data = psm.execute(data, f, cores=cores, chunksize=chunksize, name="Rotation", progress=progress,
                           msg=f"Rotating by {angle} degrees")

    return data
