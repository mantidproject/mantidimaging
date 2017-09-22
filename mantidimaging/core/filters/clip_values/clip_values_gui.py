from __future__ import absolute_import, division, print_function

from functools import partial

from PyQt5 import Qt

from mantidimaging.core.algorithms import gui_compile_ui as gcu
from mantidimaging.gui.algorithm_dialog import AlgorithmDialog

from . import clip_values

GUI_MENU_NAME = 'Clip Values'


def _gui_register(main_window):
    dialog = AlgorithmDialog(main_window)
    dialog.setWindowTitle(GUI_MENU_NAME)

    label_clip_min = Qt.QLabel("Clip Min")
    label_clip_max = Qt.QLabel("Clip Max")

    clip_min_field = Qt.QDoubleSpinBox()
    clip_min_field.setDecimals(7)
    clip_min_field.setMinimum(-10000000)
    clip_min_field.setMaximum(10000000)

    clip_max_field = Qt.QDoubleSpinBox()
    clip_max_field.setDecimals(7)
    clip_max_field.setMinimum(-10000000)
    clip_max_field.setMaximum(10000000)

    label_clip_min_new_value = Qt.QLabel("Clip Min New Value")
    label_clip_max_new_value = Qt.QLabel("Clip Max New Value")

    clip_min_new_value_field = Qt.QDoubleSpinBox()
    clip_min_new_value_field.setDecimals(7)
    clip_min_new_value_field.setMinimum(-10000000)
    clip_min_new_value_field.setMaximum(10000000)

    clip_max_new_value_field = Qt.QDoubleSpinBox()
    clip_max_new_value_field.setDecimals(7)
    clip_max_new_value_field.setMinimum(-10000000)
    clip_max_new_value_field.setMaximum(10000000)

    # The code below ensures that the new_value fields are set to be clip_min or clip_max,
    # unless the user has explicitly changed them
    def updateFieldOnValueChanged(field, field_new_value):
        field_new_value.setValue(field.value())

    # using lambda we can pass in parameters
    clip_min_field.valueChanged.connect(lambda: updateFieldOnValueChanged(clip_min_field, clip_min_new_value_field))
    clip_max_field.valueChanged.connect(lambda: updateFieldOnValueChanged(clip_max_field, clip_max_new_value_field))

    dialog.formLayout.addRow(label_clip_min, clip_min_field)
    dialog.formLayout.addRow(label_clip_max, clip_max_field)
    dialog.formLayout.addRow(label_clip_min_new_value, clip_min_new_value_field)
    dialog.formLayout.addRow(label_clip_max_new_value, clip_max_new_value_field)

    def custom_execute():
        # When called it will read the values off the dialog's fields and decorate the function
        clip_min = clip_min_field.value()
        clip_max = clip_max_field.value()
        clip_min_new_value = clip_min_new_value_field.value()
        clip_max_new_value = clip_max_new_value_field.value()
        return partial(clip_values.execute,
                       clip_min=clip_min,
                       clip_max=clip_max,
                       clip_min_new_value=clip_min_new_value,
                       clip_max_new_value=clip_max_new_value)

    # replace dialog function with this one
    dialog.set_execute(custom_execute)
    return dialog
