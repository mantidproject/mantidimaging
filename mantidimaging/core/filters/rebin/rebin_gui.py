from functools import partial

from . import execute, modes, NAME


def _gui_register(main_window):
    from PyQt5 import Qt
    from mantidimaging.gui.algorithm_dialog import AlgorithmDialog

    dialog = AlgorithmDialog(main_window)
    dialog.setWindowTitle(NAME)

    # Rebin by uniform factor options
    _, factor = dialog.add_property('Factor', 'float', 0.5, (0.0, 1.0), False)
    factor.setSingleStep(0.05)

    # Rebin to target shape options
    shape_range = (0, 9999)

    _, shape_x = dialog.add_property(
            'X', 'int', valid_values=shape_range, add_to_form=False)

    _, shape_y = dialog.add_property(
            'Y', 'int', valid_values=shape_range, add_to_form=False)

    shape_fields = Qt.QHBoxLayout()
    shape_fields.addWidget(shape_x)
    shape_fields.addWidget(shape_y)

    # Rebin dimension selection options
    rebin_by_factor_radio = Qt.QRadioButton("Rebin by Factor")

    def size_by_factor_toggled(enabled):
        factor.setEnabled(enabled)
    rebin_by_factor_radio.toggled.connect(size_by_factor_toggled)

    rebin_to_dimensions_radio = Qt.QRadioButton("Rebin to Dimensions")

    def size_by_dimensions_toggled(enabled):
        shape_x.setEnabled(enabled)
        shape_y.setEnabled(enabled)
    rebin_to_dimensions_radio.toggled.connect(size_by_dimensions_toggled)

    # Rebin mode options
    label_mode = Qt.QLabel("Mode")
    mode_field = Qt.QComboBox()
    mode_field.addItems(modes())

    dialog.formLayout.addRow(rebin_to_dimensions_radio, shape_fields)
    dialog.formLayout.addRow(rebin_by_factor_radio, factor)
    dialog.formLayout.addRow(label_mode, mode_field)

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

    dialog.set_execute(custom_execute)

    return dialog
