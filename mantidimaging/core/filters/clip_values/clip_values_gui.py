from __future__ import absolute_import, division, print_function

from functools import partial

from mantidimaging.gui.algorithm_dialog import AlgorithmDialog

from . import clip_values

GUI_MENU_NAME = 'Clip Values'


def _gui_register(main_window):
    dialog = AlgorithmDialog(main_window)
    dialog.setWindowTitle(GUI_MENU_NAME)

    value_range = (-10000000, 10000000)

    _, clip_min_field = dialog.add_property(
            'Clip Min', 'float', valid_values=(value_range))
    clip_min_field.setDecimals(7)

    _, clip_max_field = dialog.add_property(
            'Clip Max', 'float', valid_values=(value_range))
    clip_max_field.setDecimals(7)

    _, clip_min_new_value_field = dialog.add_property(
            'Min Replacement Value', 'float', valid_values=(value_range),
            tooltip='The value that will be used to replace pixel values that '
                    'fall below Clip Min.')

    _, clip_max_new_value_field = dialog.add_property(
            'Max Replacement Value', 'float', valid_values=(value_range),
            tooltip='The value that will be used to replace pixel values that '
                    'are above Clip Max.')

    clip_min_new_value_field.setDecimals(7)
    clip_max_new_value_field.setDecimals(7)

    # The code below ensures that the new_value fields are set to be clip_min
    # or clip_max, unless the user has explicitly changed them
    def updateFieldOnValueChanged(field, field_new_value):
        field_new_value.setValue(field.value())

    # using lambda we can pass in parameters
    clip_min_field.valueChanged.connect(
            lambda: updateFieldOnValueChanged(
                clip_min_field, clip_min_new_value_field))
    clip_max_field.valueChanged.connect(
            lambda: updateFieldOnValueChanged(
                clip_max_field, clip_max_new_value_field))

    def custom_execute():
        # When called it will read the values off the dialog's fields and
        # decorate the function
        clip_min = clip_min_field.value()
        clip_max = clip_max_field.value()
        clip_min_new_value = clip_min_new_value_field.value()
        clip_max_new_value = clip_max_new_value_field.value()
        return partial(clip_values.execute,
                       clip_min=clip_min,
                       clip_max=clip_max,
                       clip_min_new_value=clip_min_new_value,
                       clip_max_new_value=clip_max_new_value)

    dialog.set_execute(custom_execute)

    return dialog
