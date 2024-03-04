# Copyright (C) 2024 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

from functools import partial
from typing import Any, Dict, TYPE_CHECKING

import numpy as np
from mantidimaging.core.parallel import shared as ps
from mantidimaging.core.operations.base_filter import BaseFilter
from mantidimaging.gui.utility.qt_helpers import Type

if TYPE_CHECKING:
    from mantidimaging.core.data import ImageStack
    from mantidimaging.gui.windows.operations import FiltersWindowView
    from PyQt5.QtWidgets import QComboBox, QDoubleSpinBox


class RescaleFilter(BaseFilter):
    """Rescales the image data to a new [0, maximum output] range.

    Intended to be used on: Any

    When: Automatically used when saving as unsigned integer image formats, to avoid clipping negative values
    """
    filter_name = 'Rescale'

    @staticmethod
    def filter_func(images: ImageStack,
                    min_input: float = 0.0,
                    max_input: float = 10000.0,
                    max_output: float = 256.0,
                    progress=None) -> ImageStack:
        """
        :param min_input: The Minimum value of the data that will be used.
                          Anything below this will be clipped to 0.
        :param max_input: Maximum value of the data that will be used. Anything
                          above it will be clipped to 0.
        :param max_output: Maximum value of the OUTPUT images. They will be
                           rescaled to range [0, MAX OUTPUT].

        :return: The ImageStack object scaled to a new range.
        """

        params = {'min_input': min_input, 'max_input': max_input, 'max_output': max_output}
        ps.run_compute_func(RescaleFilter.compute_function, len(images.data), images.data, params)
        return images

    @staticmethod
    def compute_function(index: int, array: np.ndarray, params: dict):
        min_input, max_input, max_output = params['min_input'], params['max_input'], params['max_output']
        array[index] = np.interp(array[index], [min_input, max_input], [0, max_output])

    @staticmethod
    def filter_array(image: np.ndarray, min_input: float, max_input: float, max_output: float) -> np.ndarray:
        image[:] = np.interp(image, [min_input, max_input], [0, max_output])
        return image

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
