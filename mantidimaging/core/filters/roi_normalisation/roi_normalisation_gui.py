from functools import partial

from . import execute


def _gui_register(form):
    from mantidimaging.gui.filters_window import add_property_to_form

    # TODO add label that from image will be used if nothing is selected here

    value_range = (0, 1000000)

    _, roi_left_field = add_property_to_form(
            'Left', 'int', valid_values=value_range, form=form)

    _, roi_top_field = add_property_to_form(
            'Top', 'int', valid_values=value_range, form=form)

    _, roi_right_field = add_property_to_form(
            'Right', 'int', valid_values=value_range, form=form)

    _, roi_bottom_field = add_property_to_form(
            'Bottom', 'int', valid_values=value_range, form=form)

    def custom_execute():
        roi_left = roi_left_field.value()
        roi_top = roi_top_field.value()
        roi_right = roi_right_field.value()
        roi_bottom = roi_bottom_field.value()

        if roi_left == 0 and roi_top == 0 and \
                roi_right == 0 and roi_bottom == 0:
            # dialog.request_parameter(Parameters.ROI)
            return execute
        else:
            air_region = (roi_left, roi_top, roi_right, roi_bottom)
            partial(execute, air_region=air_region)

    return (None, custom_execute, None)
