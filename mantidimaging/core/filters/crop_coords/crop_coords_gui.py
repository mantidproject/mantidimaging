from functools import partial
from typing import Tuple, Callable, Optional, Dict

from . import crop_coords


def _gui_register(form, on_change) -> Tuple[Optional[Dict], Optional[Callable], Optional[Callable], Optional[Callable]]:
    from mantidimaging.gui.windows.stack_visualiser import Parameters
    from mantidimaging.gui.utility import add_property_to_form

    add_property_to_form(
        'Select ROI on stack visualiser.', 'label', form=form)

    def custom_execute():
        return partial(crop_coords.execute_single)

    params = {
        'region_of_interest': Parameters.ROI
    }

    return params, None, custom_execute, None
