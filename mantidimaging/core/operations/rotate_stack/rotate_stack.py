# Copyright (C) 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later

from functools import partial

from skimage.transform import rotate

from mantidimaging import helper as h
from mantidimaging.core.data import Images
from mantidimaging.core.operations.base_filter import BaseFilter
from mantidimaging.core.parallel import shared_mem as psm
from mantidimaging.core.utility.progress_reporting import Progress
from mantidimaging.gui.utility.qt_helpers import Type


class RotateFilter(BaseFilter):
    """Rotates the image data by an arbitrary degree counter-clockwise.

    Intended to be used on: Projections

    When: Rarely/never, ASTRA vector geometry will take care of the tilt correction

    Caution: Manually rotating could introduce additional artifacts in the
    reconstructed volume, and it is not strictly required as using
    vector geometry will correct for the tilt without manual rotation.
    """
    filter_name = "Rotate Stack"

    @staticmethod
    def filter_func(data: Images, angle=None, dark=None, cores=None, chunksize=None, progress=None):
        """
        Rotates images by an arbitrary degree.

        :param data: stack of sample images
        :param angle: The rotation to be performed, in degrees
        :param cores: cores for parallel execution
        :param chunksize: chunk for each worker

        :return: The rotated images
        """
        h.check_data_stack(data)

        if angle:
            _execute(data.data, angle, cores, chunksize, progress)

        return data

    @staticmethod
    def register_gui(form, on_change, view):
        from mantidimaging.gui.utility import add_property_to_form

        _, angle = add_property_to_form('Angle of rotation\ncounter clockwise (degrees)',
                                        Type.FLOAT,
                                        0, (-180, 180),
                                        form=form,
                                        on_change=on_change,
                                        tooltip="How much degrees to rotate counter-clockwise")
        angle.setDecimals(7)

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


def _execute(data, angle: float, cores: int, chunksize: int, progress: Progress):
    progress = Progress.ensure_instance(progress, task_name='Rotate Stack')

    with progress:
        f = psm.create_partial(_rotate_image_inplace, fwd_func=psm.inplace, angle=angle)

        data = psm.execute(data,
                           f,
                           cores=cores,
                           chunksize=chunksize,
                           progress=progress,
                           msg=f"Rotating by {angle} degrees")

    return data
