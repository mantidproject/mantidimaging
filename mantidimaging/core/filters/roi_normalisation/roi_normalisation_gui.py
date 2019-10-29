from functools import partial
from typing import Tuple, Callable, Optional, Dict

from mantidimaging.core.utility import value_scaling

from . import execute


def _gui_register(form, on_change) -> Tuple[Optional[Dict], Optional[Callable], Optional[Callable], Optional[Callable]]:
    from mantidimaging.gui.windows.stack_visualiser import SVParameters
    from mantidimaging.gui.utility import add_property_to_form

    add_property_to_form("Select ROI on stack visualiser.", "label", form=form, on_change=on_change)

    def custom_execute():
        return partial(execute)

    params = {"air_region": SVParameters.ROI}

    def do_before() -> partial:
        return partial(value_scaling.create_factors)

    def do_after() -> partial:
        return partial(value_scaling.apply_factor)

    return params, do_before, custom_execute, do_after
