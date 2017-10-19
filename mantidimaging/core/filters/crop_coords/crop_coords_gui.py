from __future__ import absolute_import, division, print_function

from functools import partial

from . import crop_coords


def _gui_register(form):
    from mantidimaging.gui.filters_window import add_property_to_form

    valid_range = (0, 99999)

    _, left = add_property_to_form(
            'Left', 'int', valid_values=valid_range, form=form)

    _, top = add_property_to_form(
            'Top', 'int', valid_values=valid_range, form=form)

    _, right = add_property_to_form(
            'Right', 'int', valid_values=valid_range, form=form)

    _, bottom = add_property_to_form(
            'Bottom', 'int', valid_values=valid_range, form=form)

    def custom_execute():
        # Get ROI from input fields
        roi = [left.value(), top.value(), right.value(), bottom.value()]

        return partial(crop_coords._execute, region_of_interest=roi)

    return (None, custom_execute, None)
