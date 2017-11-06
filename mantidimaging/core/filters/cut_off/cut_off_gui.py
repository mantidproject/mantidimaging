from functools import partial

from . import execute


def _gui_register(form):
    from mantidimaging.gui.filters_window import add_property_to_form

    _, threshold_field = add_property_to_form(
            'Threshold', 'float', 0.95, (0.0, 1.0), form=form)
    threshold_field.setSingleStep(0.05)

    def custom_execute():
        return partial(execute, threshold=threshold_field.value())

    return (None, None, custom_execute, None)
