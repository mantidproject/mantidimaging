# Copyright (C) 2024 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

from typing import TYPE_CHECKING, Callable, List, Dict

from mantidimaging.core.parallel import shared as ps
from mantidimaging.core.operations.base_filter import BaseFilter

if TYPE_CHECKING:
    import numpy as np
    from mantidimaging.core.data import ImageStack


class ClipValuesFilter(BaseFilter):
    """Clips grey values of the image based on the parameters. Can be used to remove outliers
    and noise (e.g. negative values) from reconstructed images.

    Intended to be used on: Projections and reconstructed slices

    When: To remove a range of pixel values from the data.

    Caution: Make sure the value range does not clip information from the sample.
    """
    filter_name = "Clip Values"
    link_histograms = True

    @classmethod
    def filter_func(cls,
                    data: ImageStack,
                    clip_min=None,
                    clip_max=None,
                    clip_min_new_value=None,
                    clip_max_new_value=None,
                    progress=None):
        if clip_min is None and clip_max is None:
            raise ValueError("At least one of clip_min or clip_max must be supplied")

        params = {
            'clip_min': clip_min,
            'clip_max': clip_max,
            'clip_min_new_value': clip_min_new_value,
            'clip_max_new_value': clip_max_new_value
        }

        ps.run_compute_func(cls.compute_function, data.data.shape[0], [data.shared_array], params, progress)

        return data

    @staticmethod
    def compute_function(i: int, arrays: List[np.ndarray], params: Dict[str, any]):

        array = arrays[0][i]

        clip_min = params.get('clip_min', np.min(array))
        clip_max = params.get('clip_max', np.max(array))
        clip_min_new_value = params.get('clip_min_new_value', clip_min)
        clip_max_new_value = params.get('clip_max_new_value', clip_max)

        np.clip(array, clip_min, clip_max, out=array)
        array[array < clip_min] = clip_min_new_value
        array[array > clip_max] = clip_max_new_value

    @classmethod
    def execute_wrapper(cls,
                        clip_min_field=None,
                        clip_max_field=None,
                        clip_min_new_value_field=None,
                        clip_max_new_value_field=None) -> Callable:

        def wrapper(data: 'ImageStack', progress=None):
            clip_min = clip_min_field.value() if clip_min_field else None
            clip_max = clip_max_field.value() if clip_max_field else None
            clip_min_new_value = clip_min_new_value_field.value() if clip_min_new_value_field else None
            clip_max_new_value = clip_max_new_value_field.value() if clip_max_new_value_field else None
            return cls.filter_func(data,
                                   clip_min=clip_min,
                                   clip_max=clip_max,
                                   clip_min_new_value=clip_min_new_value,
                                   clip_max_new_value=clip_max_new_value,
                                   progress=progress)

        return wrapper

    @staticmethod
    def register_gui(form, on_change, view):
        from mantidimaging.gui.utility import add_property_to_form

        value_range = (-10000000, 10000000)

        _, clip_min_field = add_property_to_form('Clip Min',
                                                 'float',
                                                 valid_values=value_range,
                                                 form=form,
                                                 on_change=on_change,
                                                 tooltip="Any pixel with a value below this number will be clipped")
        clip_min_field.setDecimals(7)

        _, clip_max_field = add_property_to_form('Clip Max',
                                                 'float',
                                                 valid_values=value_range,
                                                 form=form,
                                                 on_change=on_change,
                                                 tooltip="Any pixel with a value above this number will be clipped")
        clip_max_field.setDecimals(7)

        _, clip_min_new_value_field = add_property_to_form(
            'Min Replacement Value',
            'float',
            valid_values=value_range,
            form=form,
            on_change=on_change,
            tooltip='The value that will be used to replace pixel values '
            'that fall below Clip Min.')

        _, clip_max_new_value_field = add_property_to_form(
            'Max Replacement Value',
            'float',
            valid_values=value_range,
            form=form,
            on_change=on_change,
            tooltip='The value that will be used to replace pixel values '
            'that are above Clip Max.')

        clip_min_new_value_field.setDecimals(7)
        clip_max_new_value_field.setDecimals(7)

        # Ensures that the new_value fields are set to be clip_min
        # or clip_max, unless the user has explicitly changed them
        def update_field_on_value_changed(field, field_new_value):
            field_new_value.setValue(field.value())

        # using lambda we can pass in parameters
        clip_min_field.valueChanged.connect(
            lambda: update_field_on_value_changed(clip_min_field, clip_min_new_value_field))
        clip_max_field.valueChanged.connect(
            lambda: update_field_on_value_changed(clip_max_field, clip_max_new_value_field))

        return {
            "clip_min_field": clip_min_field,
            "clip_max_field": clip_max_field,
            "clip_min_new_value_field": clip_min_new_value_field,
            "clip_max_new_value_field": clip_max_new_value_field
        }
