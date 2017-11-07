from functools import partial

from . import execute


def _gui_register(form, on_change):
    # Not much here, this filter does one thing and one thing only.

    def custom_execute():
        return partial(execute, minus_log=True)

    return (None, None, custom_execute, None)
