import os
from functools import partial
from typing import Tuple, Callable, Optional, Dict

from mantidimaging.core import io
from mantidimaging.core.filters.background_correction import execute
from mantidimaging.core.utility import value_scaling


def _gui_register(form, on_change) -> Tuple[Optional[Dict], Optional[Callable], Optional[Callable], Optional[Callable]]:
    from mantidimaging.gui.utility import add_property_to_form

    flatPath, _ = add_property_to_form("Flat", "file", form=form, on_change=on_change)

    darkPath, _ = add_property_to_form("Dark", "file", form=form, on_change=on_change)

    def execute_wrapper() -> partial:
        flat_path = str(flatPath.text())
        dark_path = str(darkPath.text())
        flat_extension = io.utility.get_file_extension(flat_path)
        dark_extension = io.utility.get_file_extension(dark_path)

        flat_dir = os.path.dirname(flat_path)
        dark_dir = os.path.dirname(dark_path)

        images_flat_only = io.loader.load(flat_dir, in_format=flat_extension)

        # this will be put in the 'sample' attribute, because we load a single
        # volume
        flat = images_flat_only.sample.mean(axis=0)

        images_dark_only = io.loader.load(dark_dir, in_format=dark_extension)

        # this will be put in the 'sample' attribute, because we load a single
        # volume
        dark = images_dark_only.sample.mean(axis=0)

        par = partial(execute, flat=flat, dark=dark)

        return par

    def do_before() -> partial:
        return partial(value_scaling.create_factors)

    def do_after() -> partial:
        return partial(value_scaling.apply_factor)

    return None, do_before, execute_wrapper, do_after
