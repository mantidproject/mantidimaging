# Copyright (C) 2024 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations
from typing import Union, Optional, List, TYPE_CHECKING, Callable, Dict

import numpy as np

from mantidimaging import helper as h
from mantidimaging.core.operations.base_filter import BaseFilter, FilterGroup
from mantidimaging.core.utility.progress_reporting import Progress
from mantidimaging.core.utility.sensible_roi import SensibleROI
from mantidimaging.gui.utility.qt_helpers import Type

if TYPE_CHECKING:
    from mantidimaging.core.data import ImageStack
    from PyQt5.QtWidgets import QLineEdit, QFormLayout, QWidget
    from mantidimaging.gui.mvp_base import BaseMainWindowView


class CropCoordinatesFilter(BaseFilter):
    """Crop a region of interest from the image.

    Intended to be used on: A stack of projections, or reconstructed slices

    When: To select part of the image that is to be processed further; this reduces
    memory usage and can greatly improve the speed of reconstruction.

    Caution: Make sure the region of cropping does not crop parts of the sample
    during the rotation of the sample in the dataset.
    """
    filter_name = "Crop Coordinates"
    link_histograms = True

    @classmethod
    def filter_func(cls,
                    images: ImageStack,
                    region_of_interest: Optional[Union[List[int], List[float], 'SensibleROI']] = None,
                    progress=None) -> ImageStack:
        """Execute the Crop Coordinates by Region of Interest filter. This does
        NOT do any checks if the Region of interest is out of bounds!

        If the region of interest is out of bounds, the crop will **FAIL** at
        runtime.

        If the region of interest is in bounds, but has overlapping coordinates
        the crop give back a 0 shape of the coordinates that were wrong.

        :param images: Input data as a 3D numpy.ndarray

        :param region_of_interest: Crop original images using these coordinates.
                                   The selection is a rectangle and expected order
                                   is - Left Top Right Bottom.

        :return: The processed 3D numpy.ndarray
        """

        if region_of_interest is None:
            region_of_interest = SensibleROI.from_list([0, 0, 50, 50])
        if isinstance(region_of_interest, list):
            region_of_interest = SensibleROI.from_list(region_of_interest)

        assert isinstance(region_of_interest, SensibleROI)

        h.check_data_stack(images)

        sample = images.data
        shape = (sample.shape[0], region_of_interest.height, region_of_interest.width)
        if any((s <= 0 for s in shape[1:])):
            raise ValueError("It seems the Region of Interest is outside of the current image dimensions.\n"
                             "This can happen on the image preview right after a previous Crop Coordinates.")
        params = {'roi': region_of_interest}
        output = np.empty(shape, dtype=images.data.dtype)
        cls.compute_function(images.data.shape[0], images.data, params, output, progress)
        images.data = output
        return images

    @staticmethod
    def compute_function(num_images: int,
                         input_array: np.ndarray,
                         params: Dict[str, any],
                         output_array: np.ndarray,
                         progress=None):
        roi = params['roi']
        for i in range(num_images):
            output_array[i] = input_array[i, roi.top:roi.bottom, roi.left:roi.right]
            if progress is not None:
                progress.update(i / num_images)

    @staticmethod
    def register_gui(form: 'QFormLayout', on_change: Callable, view: 'BaseMainWindowView') -> Dict[str, 'QWidget']:
        from mantidimaging.gui.utility import add_property_to_form
        label, roi_field = add_property_to_form("ROI",
                                                Type.STR,
                                                form=form,
                                                on_change=on_change,
                                                default_value="0, 0, 200, 200")
        roi_button, _ = add_property_to_form("Select ROI", Type.BUTTON, form=form, on_change=on_change)
        roi_button.clicked.connect(lambda: view.roi_visualiser(roi_field, roi_button))

        return {'roi_field': roi_field}

    @staticmethod
    def execute_wrapper(cls, roi_field: QLineEdit) -> Callable:
        try:
            roi = SensibleROI.from_list([int(number) for number in roi_field.text().strip("[").strip("]").split(",")])
            return cls.filter_func(region_of_interest=roi)
        except Exception as exc:
            raise ValueError(f"The provided ROI string is invalid! Error: {exc}") from exc

    @staticmethod
    def group_name() -> FilterGroup:
        return FilterGroup.Basic


def execute_single(data, roi, progress=None, out=None):
    progress = Progress.ensure_instance(progress, task_name='Crop Coords')

    if roi:
        progress.add_estimated_steps(1)

        with progress:
            assert all(isinstance(region, int) for
                       region in roi), \
                "The region of interest coordinates are not integers!"

            progress.update(msg="Cropping with coordinates: {0}".format(roi))

            output = out[:] if out is not None else data[:]
            output[:] = data[:, roi.top:roi.bottom, roi.left:roi.right]
        return output
