from __future__ import absolute_import, division, print_function

from functools import partial

from . import execute


def _gui_register(form, on_change):
    from mantidimaging.gui.utility import add_property_to_form

    _, radius_field = add_property_to_form(
            'Radius', 'float', 0.95, (0.0, 1.0),
            form=form, on_change=on_change)

    _, value_field = add_property_to_form(
            'Set to value', 'float', 0, (-10000, 10000),
            form=form, on_change=on_change)

    def custom_execute():
        return partial(execute,
                       circular_mask_ratio=radius_field.value(),
                       circular_mask_value=value_field.value())

    return (None, None, custom_execute, None)
