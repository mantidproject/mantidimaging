# Copyright (C) 2024 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

from functools import partial
from typing import TYPE_CHECKING, List, Dict, Any

import numpy as np
import tomopy

from mantidimaging.core.parallel import shared as ps
from mantidimaging.core.operations.base_filter import BaseFilter
from mantidimaging.gui.utility.qt_helpers import Type

if TYPE_CHECKING:
    from mantidimaging.core.data import ImageStack


class CircularMaskFilter(BaseFilter):
    """Masks a circular area around the center of the image, by setting it to a
    specified value.

    Intended to be used on: Reconstructed slices

    When: To remove reconstruction artifacts on the outer edge of the image.

    Caution: Ensure that the radius does not mask data from the sample.
    """
    filter_name = "Circular Mask"
    link_histograms = True

    @staticmethod
    def filter_func(data: ImageStack, circular_mask_ratio=0.95, circular_mask_value=0., progress=None) -> ImageStack:
        """
        :param data: Input data as a 3D numpy.ndarray
        :param circular_mask_ratio: The ratio to the full image.
    @@ -39,20 +41,21 @@ def filter_func(data: ImageStack, circular_mask_ratio=0.95, circular_mask_value=
        :return: The processed 3D numpy.ndarray
        """
        if not 0 < circular_mask_ratio < 1:
            raise ValueError(
                f"Circular mask ratio must be greater than 0 and less than 1, but value was {circular_mask_ratio}")

        params = {'circular_mask_ratio': circular_mask_ratio, 'circular_mask_value': circular_mask_value}

        ps.run_compute_func(CircularMaskFilter.compute_function, data.data.shape[0], [data.shared_array], params,
                            progress)

        return data

    @staticmethod
    def compute_function(i: int, arrays: List[np.ndarray], params: Dict[str, Any]):
        tomopy.circ_mask(arrays[0][i], axis=0, ratio=params['circular_mask_ratio'], val=params['circular_mask_value'])

    @staticmethod
    def register_gui(form, on_change, view):
        from mantidimaging.gui.utility import add_property_to_form

        _, radius_field = add_property_to_form('Radius',
                                               Type.FLOAT,
                                               0.95, (0.01, 0.99),
                                               form=form,
                                               on_change=on_change,
                                               tooltip="Radius [0, 1] of image that should be left untouched.")

        _, value_field = add_property_to_form('Set to value',
                                              Type.FLOAT,
                                              0, (-10000, 10000),
                                              form=form,
                                              on_change=on_change,
                                              tooltip="The value of the mask.")

        return {'radius_field': radius_field, 'value_field': value_field}

    @staticmethod
    def execute_wrapper(radius_field=None, value_field=None):
        return partial(CircularMaskFilter.filter_func,
                       circular_mask_ratio=radius_field.value(),
                       circular_mask_value=value_field.value())
