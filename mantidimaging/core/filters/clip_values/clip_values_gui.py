from __future__ import absolute_import, division, print_function

from functools import partial

from . import execute


def _gui_register(form):
    from mantidimaging.gui.utility import add_property_to_form

    value_range = (-10000000, 10000000)

    _, clip_min_field = add_property_to_form(
            'Clip Min', 'float', valid_values=(value_range), form=form)
    clip_min_field.setDecimals(7)

    _, clip_max_field = add_property_to_form(
            'Clip Max', 'float', valid_values=(value_range), form=form)
    clip_max_field.setDecimals(7)

    _, clip_min_new_value_field = add_property_to_form(
            'Min Replacement Value', 'float', valid_values=(value_range),
            form=form, tooltip='The value that will be used to replace pixel '
                               'values that fall below Clip Min.')

    _, clip_max_new_value_field = add_property_to_form(
            'Max Replacement Value', 'float', valid_values=(value_range),
            form=form, tooltip='The value that will be used to replace pixel '
                               'values that are above Clip Max.')

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
        return partial(execute,
                       clip_min=clip_min,
                       clip_max=clip_max,
                       clip_min_new_value=clip_min_new_value,
                       clip_max_new_value=clip_max_new_value)

    return (None, None, custom_execute, None)
