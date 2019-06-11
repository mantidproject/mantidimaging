from functools import partial
from typing import Tuple, Callable, Optional, Dict

from . import execute


def _gui_register(form, on_change) -> Tuple[Optional[Dict], Optional[Callable], Optional[Callable], Optional[Callable]]:
    from mantidimaging.gui.utility import add_property_to_form

    _, rotation_count = add_property_to_form(
        'Number of rotations', 'int', 1, (0, 99),
        form=form, on_change=on_change)

    def custom_execute():
        num_rotations = rotation_count.value()
        return partial(execute, rotation=num_rotations)

    return None, None, custom_execute, None
