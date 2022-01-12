# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later

from functools import partial
import numpy as np

from skimage.transform import rotate

from mantidimaging import helper as h
from mantidimaging.core.data import Images
from mantidimaging.core.operations.base_filter import BaseFilter
from mantidimaging.core.parallel import shared as ps
from mantidimaging.core.utility.progress_reporting import Progress
from mantidimaging.gui.utility.qt_helpers import Type


class RotateFilter(BaseFilter):
    """Rotates the image data by an arbitrary degree counter-clockwise.

    Intended to be used on: Projections

    When: 90 or 270 degree rotation for rotation axis to be vertical for some camera types.

    Caution: Rotations of images others than multiples of 90 degrees could introduce additional
    artifacts in the reconstructed volume. Such rotations are usually not required as
    small tilts can be taken into account at the reconstruction stage.
    """
    filter_name = "Rotate Stack"
    link_histograms = True

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

        if angle is None:
            raise ValueError('Value must be provided for angle parameter')

        # No need to run the filter for an angle of 0 as it won't have any effect
        if not angle == 0:
            _execute(data.data, angle, cores, chunksize, progress)

        return data

    @staticmethod
    def register_gui(form, on_change, view):
        from mantidimaging.gui.utility import add_property_to_form

        _, angle = add_property_to_form('Angle of rotation\ncounter clockwise (degrees)',
                                        Type.FLOAT,
                                        0, (-359, 359),
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


def _execute(data: np.ndarray, angle: float, cores: int, chunksize: int, progress: Progress):
    progress = Progress.ensure_instance(progress, task_name='Rotate Stack')

    with progress:
        f = ps.create_partial(_rotate_image_inplace, ps.inplace1, angle=angle)
        ps.shared_list = [data]
        ps.execute(f, data.shape[0], progress, msg=f"Rotating by {angle} degrees", cores=cores)

    return data
