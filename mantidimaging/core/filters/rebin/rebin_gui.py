from functools import partial
from typing import Tuple, Callable, Optional, Dict

from . import execute, modes


def _gui_register(form, on_change) -> Tuple[Optional[Dict], Optional[Callable], Optional[Callable], Optional[Callable]]:
    from PyQt5 import Qt
    from mantidimaging.gui.utility import add_property_to_form

    # Rebin by uniform factor options
    _, factor = add_property_to_form(
        'Factor', 'float', 0.5, (0.0, 1.0),
        on_change=on_change)
    factor.setSingleStep(0.05)

    # Rebin to target shape options
    shape_range = (0, 9999)

    _, shape_x = add_property_to_form(
        'X', 'int',
        valid_values=shape_range,
        on_change=on_change)
    _, shape_y = add_property_to_form(
        'Y', 'int',
        valid_values=shape_range,
        on_change=on_change)

    shape_fields = Qt.QHBoxLayout()
    shape_fields.addWidget(shape_x)
    shape_fields.addWidget(shape_y)

    # Rebin dimension selection options
    rebin_by_factor_radio = Qt.QRadioButton("Rebin by Factor")

    def size_by_factor_toggled(enabled):
        factor.setEnabled(enabled)
        on_change()

    rebin_by_factor_radio.toggled.connect(size_by_factor_toggled)

    rebin_to_dimensions_radio = Qt.QRadioButton("Rebin to Dimensions")

    def size_by_dimensions_toggled(enabled):
        shape_x.setEnabled(enabled)
        shape_y.setEnabled(enabled)
        on_change()

    rebin_to_dimensions_radio.toggled.connect(size_by_dimensions_toggled)

    # Rebin mode options
    label_mode = Qt.QLabel("Mode")
    mode_field = Qt.QComboBox()
    mode_field.addItems(modes())

    form.addRow(rebin_to_dimensions_radio, shape_fields)
    form.addRow(rebin_by_factor_radio, factor)
    form.addRow(label_mode, mode_field)

    # Ensure good default UI state
    rebin_to_dimensions_radio.setChecked(True)
    rebin_by_factor_radio.setChecked(True)

    def custom_execute():
        if rebin_to_dimensions_radio.isChecked():
            params = (shape_x.value(), shape_y.value())
        elif rebin_by_factor_radio.isChecked():
            params = factor.value()
        else:
            raise ValueError('Unknown bin dimension mode')

        return partial(execute,
                       mode=mode_field.currentText(),
                       rebin_param=params)

    return None, None, custom_execute, None
