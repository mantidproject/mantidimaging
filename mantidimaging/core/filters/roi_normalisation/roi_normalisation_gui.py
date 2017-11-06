from functools import partial

from mantidimaging.gui.stack_visualiser import Parameters

from . import execute


def _gui_register(form):
    from mantidimaging.gui.filters_window import add_property_to_form

    add_property_to_form(
            'Select ROI on stack visualiser.', 'label', form=form)

    def custom_execute():
        return partial(execute)

    params = {
        'air_region': Parameters.ROI
    }

    return (params, None, custom_execute, None)
