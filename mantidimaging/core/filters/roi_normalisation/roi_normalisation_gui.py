from functools import partial

from mantidimaging.core.utility import value_scaling
from . import execute


def _gui_register(form, on_change):
    from mantidimaging.gui.windows.stack_visualiser import Parameters
    from mantidimaging.gui.utility import add_property_to_form

    add_property_to_form(
        'Select ROI on stack visualiser.', 'label',
        form=form, on_change=on_change)

    def custom_execute():
        return partial(execute)

    def custom_do_before() -> partial:
        return partial(value_scaling.create_factors)

    def custom_do_after() -> partial:
        return partial(value_scaling.apply_factor)

    params = {
        'air_region': Parameters.ROI
    }

    return params, custom_do_before, custom_execute, custom_do_after
