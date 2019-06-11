from functools import partial
from typing import Tuple, Callable, Optional, Dict

from . import execute


def _gui_register(form, on_change) -> Tuple[Optional[Dict], Optional[Callable], Optional[Callable], Optional[Callable]]:
    from mantidimaging.gui.utility import add_property_to_form

    _, threshold_field = add_property_to_form(
        'Threshold', 'float', 0.95, (0.0, 1.0),
        form=form, on_change=on_change)
    threshold_field.setSingleStep(0.05)

    def custom_execute():
        return partial(execute, threshold=threshold_field.value())

    return None, None, custom_execute, None
