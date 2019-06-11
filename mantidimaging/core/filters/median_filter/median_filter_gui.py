from functools import partial
from typing import Tuple, Callable, Optional, Dict

from . import execute, modes


def _gui_register(form, on_change) -> Tuple[Optional[Dict], Optional[Callable], Optional[Callable], Optional[Callable]]:
    from mantidimaging.gui.utility import add_property_to_form

    _, size_field = add_property_to_form(
        'Kernel Size', 'int', 3, (0, 1000),
        form=form, on_change=on_change)

    _, mode_field = add_property_to_form(
        'Mode', 'list', valid_values=modes(),
        form=form, on_change=on_change)

    def custom_execute():
        return partial(execute,
                       size=size_field.value(),
                       mode=mode_field.currentText())

    return None, None, custom_execute, None
