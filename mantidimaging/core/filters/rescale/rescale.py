from functools import partial
from typing import Dict, Any

import numpy as np
from PyQt5.QtWidgets import QDoubleSpinBox, QComboBox

from mantidimaging.core.data import Images
from mantidimaging.core.filters.base_filter import BaseFilter
from mantidimaging.gui.utility.qt_helpers import Type
from mantidimaging.gui.windows.filters import FiltersWindowView


class RescaleFilter(BaseFilter):
    filter_name = 'Rescale'

    @staticmethod
    def filter_func(images: Images, min_output: float, max_output: float, progress=None) -> Images:
        # images.data[images.data < min_output] = min_output
        np.clip(images.data, min_output, None, out=images.data)
        images.data *= (max_output / images.data.max())
        return images

    @staticmethod
    def register_gui(form, on_change, view: FiltersWindowView) -> Dict[str, Any]:
        from mantidimaging.gui.utility import add_property_to_form
        _, min_output_widget = add_property_to_form('Min output', Type.FLOAT, form=form, on_change=on_change,
                                                    valid_values=(0, 2147483647))
        _, max_output_widget = add_property_to_form('Max output', Type.FLOAT, form=form, on_change=on_change,
                                                    default_value=65535.0,
                                                    valid_values=(1, 2147483647))
        _, preset_widget = add_property_to_form('Preset', Type.CHOICE, form=form, on_change=on_change,
                                                valid_values=["Use values from above", "int8", "int16", "int32"])

        return {
            'min_output_widget': min_output_widget,
            'max_output_widget': max_output_widget,
            'preset_widget': preset_widget
        }

    @staticmethod
    def execute_wrapper(min_output_widget: QDoubleSpinBox, max_output_widget: QDoubleSpinBox,
                        preset_widget: QComboBox) -> partial:
        min_output = min_output_widget.value()
        max_output = max_output_widget.value()

        if preset_widget.currentText() == "int8":
            min_output = 0.0
            max_output = 255.0
        elif preset_widget.currentText() == "int16":
            min_output = 0.0
            max_output = 65535.0
        elif preset_widget.currentText() == "int32":
            min_output = 0.0
            max_output = 2147483647.0

        return partial(RescaleFilter.filter_func, min_output=min_output, max_output=max_output)

    @staticmethod
    def validate_execute_kwargs(kwargs: Dict[str, Any]) -> bool:
        return True
