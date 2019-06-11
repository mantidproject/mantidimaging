from functools import partial
from typing import Tuple, Callable, Optional, Dict

from . import execute


def _gui_register(form, on_change) -> Tuple[Optional[Dict], Optional[Callable], Optional[Callable], Optional[Callable]]:
    from mantidimaging.gui.windows.stack_visualiser import Parameters
    from mantidimaging.gui.utility import add_property_to_form

    add_property_to_form(
        'Select ROI on stack visualiser.', 'label',
        form=form, on_change=on_change)

    def custom_execute():
        return partial(execute)

    params = {
        'air_region': Parameters.ROI
    }

    return params, None, custom_execute, None
