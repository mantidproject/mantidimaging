# Copyright (C) 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later

from functools import partial
from typing import Any, Dict

import numpy as np
from numpy import float32, nanmax, nanmin, ndarray, uint16
from PyQt5.QtWidgets import QComboBox, QDoubleSpinBox

from mantidimaging.core.data import Images
from mantidimaging.core.operations.base_filter import BaseFilter
from mantidimaging.gui.utility.qt_helpers import Type
from mantidimaging.gui.windows.operations import FiltersWindowView


class RescaleFilter(BaseFilter):
    """Rescales the image data to a new [0, maximum output] range.

    Intended to be used on: Any

    When: Can be used to crop-out value regions of interest

    When: Automatically used when saving images to uint16
    """
    filter_name = 'Rescale'

    @staticmethod
    def filter_func(images: Images,
                    min_input: float = 0.0,
                    max_input: float = 10000.0,
                    max_output: float = 256.0,
                    progress=None,
                    data_type=None) -> Images:
        np.clip(images.data, min_input, max_input, out=images.data)
        # offset - it removes any negative values so that they don't overflow when in uint16 range
        images.data -= nanmin(images.data)
        data_max = nanmax(images.data)
        # slope
        images.data *= (max_output / data_max)

        if data_type is not None:
            if data_type == uint16 and not images.dtype == uint16:
                images.data = images.data.astype(uint16)
            elif data_type == float32 and not images.dtype == float32:
                images.data = images.data.astype(float32)

        return images

    @staticmethod
    def filter_single_image(image: ndarray, min_input: float, max_input: float, max_output: float, data_type=float32):
        np.clip(image, min_input, max_input, out=image)
        image -= min_input
        data_max = nanmax(image)

        image *= (max_output / data_max)

        if data_type == float32:
            return image.astype(float32)
        elif data_type == uint16:
            return image.astype(uint16)
        else:
            raise ValueError("Only float32 and int16 data types are supported by single image rescale")

    @staticmethod
    def register_gui(form, on_change, view: FiltersWindowView) -> Dict[str, Any]:
        from mantidimaging.gui.utility import add_property_to_form
        _, min_input_widget = add_property_to_form('Min input',
                                                   Type.FLOAT,
                                                   form=form,
                                                   on_change=on_change,
                                                   valid_values=(-2147483647, 2147483647),
                                                   tooltip="Minimum value of the data that will be used.\n"
                                                   "Anything below this will be clipped to 0")
        min_input_widget.setDecimals(8)
        _, max_input_widget = add_property_to_form('Max input',
                                                   Type.FLOAT,
                                                   form=form,
                                                   on_change=on_change,
                                                   default_value=5.0,
                                                   valid_values=(-2147483647, 2147483647),
                                                   tooltip="Maximum value of the data that will be used.\n"
                                                   "Anything above it will be clipped to 0")
        max_input_widget.setDecimals(8)
        _, max_output_widget = add_property_to_form('Max output',
                                                    Type.FLOAT,
                                                    form=form,
                                                    on_change=on_change,
                                                    default_value=65535.0,
                                                    valid_values=(1, 2147483647),
                                                    tooltip="Maximum value of the OUTPUT images. They will \n"
                                                    "be rescaled to range [0, MAX OUTPUT]")
        max_output_widget.setDecimals(8)
        _, preset_widget = add_property_to_form('Preset',
                                                Type.CHOICE,
                                                form=form,
                                                on_change=on_change,
                                                valid_values=["Use values from above", "int8", "int16", "int32"],
                                                tooltip="Provides pre-set ranges to rescale to.")

        return {
            'min_input_widget': min_input_widget,
            'max_input_widget': max_input_widget,
            'max_output_widget': max_output_widget,
            'preset_widget': preset_widget
        }

    @staticmethod
    def execute_wrapper(  # type: ignore
            min_input_widget: QDoubleSpinBox, max_input_widget: QDoubleSpinBox, max_output_widget: QDoubleSpinBox,
            preset_widget: QComboBox) -> partial:
        min_input = min_input_widget.value()
        max_input = max_input_widget.value()
        max_output = max_output_widget.value()

        if preset_widget.currentText() == "int8":
            max_output = 255.0
        elif preset_widget.currentText() == "int16":
            max_output = 65535.0
        elif preset_widget.currentText() == "int32":
            max_output = 2147483647.0

        return partial(RescaleFilter.filter_func, min_input=min_input, max_input=max_input, max_output=max_output)

    @staticmethod
    def validate_execute_kwargs(kwargs: Dict[str, Any]) -> bool:
        return True
