from functools import partial

from . import execute, modes


def _gui_register(form, on_change):
    from mantidimaging.gui.utility import add_property_to_form

    _, size_field = add_property_to_form(
            'Kernel Size', 'int', 3, (0, 1000),
            form=form, on_change=on_change)

    _, order_field = add_property_to_form(
            'Order', 'int', 0, (0, 3),
            form=form, on_change=on_change)

    _, mode_field = add_property_to_form(
            'Mode', 'list', valid_values=modes(),
            form=form, on_change=on_change)

    def custom_execute():
        return partial(execute,
                       size=size_field.value(),
                       mode=mode_field.currentText(),
                       order=order_field.value())

    return (None, None, custom_execute, None)
