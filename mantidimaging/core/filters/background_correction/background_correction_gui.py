import os
from functools import partial
from typing import Callable, Dict, Optional, Tuple

from mantidimaging.core import io
from mantidimaging.core.filters.background_correction import execute
from mantidimaging.core.utility import value_scaling


def _gui_register(form, on_change) -> Tuple[Optional[Dict], Optional[Callable], Optional[Callable], Optional[Callable]]:
    from mantidimaging.gui.utility import add_property_to_form

    flatPath, _ = add_property_to_form("Flat", "file", form=form, on_change=on_change)

    darkPath, _ = add_property_to_form("Dark", "file", form=form, on_change=on_change)

    def execute_wrapper() -> partial:
        flat_path = str(flatPath.text())
        flat_extension = io.utility.get_file_extension(flat_path)
        flat_prefix = io.utility.get_prefix(flat_path)

        flat_dir = os.path.dirname(flat_path)

        images_flat_only = io.loader.load(flat_dir, flat_prefix, flat_extension)

        # this will be put in the 'sample' attribute, because we load a single
        # volume
        flat = images_flat_only.sample.mean(axis=0)

        dark_path = str(darkPath.text())
        dark_extension = io.utility.get_file_extension(dark_path)
        dark_dir = os.path.dirname(dark_path)
        dark_prefix = io.utility.get_prefix(dark_path)
        images_dark_only = io.loader.load(dark_dir, dark_prefix, dark_extension)

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
