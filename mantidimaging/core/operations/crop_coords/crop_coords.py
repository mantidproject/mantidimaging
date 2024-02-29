# Copyright (C) 2024 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

from functools import partial
from typing import Union, Optional, List, TYPE_CHECKING, Dict, Any

import numpy as np

from mantidimaging import helper as h
from mantidimaging.core.parallel import utility as pu, shared as ps
from mantidimaging.core.operations.base_filter import BaseFilter, FilterGroup
from mantidimaging.core.utility.sensible_roi import SensibleROI
from mantidimaging.gui.utility.qt_helpers import Type

if TYPE_CHECKING:
    from mantidimaging.core.data import ImageStack
    from PyQt5.QtWidgets import QLineEdit


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

    @staticmethod
    def filter_func(images: ImageStack,
                    region_of_interest: Optional[Union[List[int], List[float], SensibleROI]] = None,
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
        if any((s < 0 for s in shape)):
            raise ValueError("It seems the Region of Interest is outside of the current image dimensions.\n"
                             "This can happen on the image preview right after a previous Crop Coordinates.")

        output = pu.create_array(shape, images.dtype)
        params = {'sample': sample, 'roi': region_of_interest, 'output': output.array}
        ps.run_compute_func(CropCoordinatesFilter.compute_function, sample.shape[0], images.shared_array, params,
                            progress)
        images.shared_array = output
        return images

    @staticmethod
    def compute_function(i: int, array: np.ndarray, params: Dict[str, Any]):
        _ = array
        sample = params['sample']
        roi = params['roi']
        output = params['output']
        if isinstance(roi, SensibleROI):
            left, top, right, bottom = roi.left, roi.top, roi.right, roi.bottom
        else:
            left, top, right, bottom = roi[0], roi[1], roi[2], roi[3]
        output[i] = sample[i, top:bottom, left:right]

    def register_gui(form, on_change, view):
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
    def execute_wrapper(roi_field: QLineEdit) -> partial:
        try:
            roi = SensibleROI.from_list([int(number) for number in roi_field.text().strip("[").strip("]").split(",")])
            return partial(CropCoordinatesFilter.filter_func, region_of_interest=roi)
        except Exception as exc:
            raise ValueError(f"The provided ROI string is invalid! Error: {exc}") from exc

    @staticmethod
    def group_name() -> FilterGroup:
        return FilterGroup.Basic
