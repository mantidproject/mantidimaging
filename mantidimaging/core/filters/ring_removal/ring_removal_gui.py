from functools import partial

from . import execute


def _gui_register(form):
    from mantidimaging.gui.utility import add_property_to_form

    range1 = (0, 1000000)
    range2 = (-1000000, 1000000)

    _, x_field = add_property_to_form(
            'Abcissa X', 'int', valid_values=range1, form=form)

    _, y_field = add_property_to_form(
            'Ordinate Y', 'int', valid_values=range1, form=form)

    _, thresh = add_property_to_form(
            'Threshold', 'float', valid_values=range2, form=form)

    _, thresh_min = add_property_to_form(
            'Threshold Min', 'float', valid_values=range2, form=form)

    _, thresh_max = add_property_to_form(
            'Threshold Max', 'float', valid_values=range2, form=form)

    _, theta = add_property_to_form(
            'Theta', 'int', valid_values=(-1000, 1000), form=form)

    _, rwidth = add_property_to_form(
            'RWidth', 'int', valid_values=range2, form=form)

    def custom_execute():
        return partial(execute,
                       run_ring_removal=True,
                       center_x=x_field,
                       center_y=y_field,
                       thresh=thresh,
                       thresh_max=thresh_max,
                       thresh_min=thresh_min,
                       theta_min=theta,
                       rwidth=rwidth)

    return (None, None, custom_execute, None)
