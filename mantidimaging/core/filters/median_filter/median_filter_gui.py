from functools import partial

from . import execute, modes


def _gui_register(form):
    from mantidimaging.gui.filters_window import add_property_to_form

    _, size_field = add_property_to_form(
            'Kernel Size', 'int', 3, (0, 1000), form=form)

    _, mode_field = add_property_to_form(
            'Mode', 'list', valid_values=modes(), form=form)

    def custom_execute():
        return partial(execute,
                       size=size_field.value(),
                       mode=mode_field.currentText())

    return (None, custom_execute, None)
