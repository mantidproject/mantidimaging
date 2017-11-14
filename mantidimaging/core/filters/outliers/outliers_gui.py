from functools import partial

from . import execute, modes


def _gui_register(form, on_change):
    from mantidimaging.gui.utility import add_property_to_form

    _, diff_field = add_property_to_form(
            'Difference', 'int', 1, (-1000000, 1000000),
            form=form, on_change=on_change)

    _, size_field = add_property_to_form(
            'Size', 'int', 3, (0, 1000),
            form=form, on_change=on_change)

    _, mode_field = add_property_to_form(
            'Mode', 'list', valid_values=modes(),
            form=form, on_change=on_change)

    def custom_execute():
        return partial(execute,
                       diff=diff_field.value(),
                       radius=size_field.value(),
                       mode=mode_field.currentText())

    return (None, None, custom_execute, None)
