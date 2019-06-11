from functools import partial
from typing import Tuple, Callable, Optional, Dict

from . import execute


def _gui_register(form, on_change) -> Tuple[Optional[Dict], Optional[Callable], Optional[Callable], Optional[Callable]]:
    # Not much here, this filter does one thing and one thing only.

    def custom_execute():
        return partial(execute, minus_log=True)

    return None, None, custom_execute, None
