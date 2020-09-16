from functools import partial
from typing import Dict, Any
from numpy import issubdtype, int16, float32

from PyQt5.QtWidgets import QDoubleSpinBox, QComboBox

from mantidimaging.core.data import Images
from mantidimaging.core.operations.base_filter import BaseFilter
from mantidimaging.gui.utility.qt_helpers import Type
from mantidimaging.gui.windows.operations import FiltersWindowView


class RescaleFilter(BaseFilter):
    filter_name = 'Rescale'

    @staticmethod
    def filter_func(images: Images,
                    min_input: float = 0.0,
                    max_input: float = 10000.0,
                    max_output: float = 256.0,
                    progress=None,
                    data_type=float32) -> Images:
        images.data[images.data < min_input] = 0
        images.data[images.data > max_input] = 0
        images.data *= (max_output / images.data.max())

        if data_type == int16 and not images.dtype == int16:
            images.data = images.data.astype(int16)
        elif data_type == float32 and not images.dtype == float32:
            images.data = images.data.astype(float32)

        return images

    @staticmethod
    def register_gui(form, on_change, view: FiltersWindowView) -> Dict[str, Any]:
        from mantidimaging.gui.utility import add_property_to_form
        _, min_input_widget = add_property_to_form('Min input',
                                                   Type.FLOAT,
                                                   form=form,
                                                   on_change=on_change,
                                                   valid_values=(-2147483647, 2147483647))
        _, max_input_widget = add_property_to_form('Max input',
                                                   Type.FLOAT,
                                                   form=form,
                                                   on_change=on_change,
                                                   default_value=5.0,
                                                   valid_values=(-2147483647, 2147483647))
        _, max_output_widget = add_property_to_form('Max output',
                                                    Type.FLOAT,
                                                    form=form,
                                                    on_change=on_change,
                                                    default_value=65535.0,
                                                    valid_values=(1, 2147483647))
        _, preset_widget = add_property_to_form('Preset',
                                                Type.CHOICE,
                                                form=form,
                                                on_change=on_change,
                                                valid_values=["Use values from above", "int8", "int16", "int32"])

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
