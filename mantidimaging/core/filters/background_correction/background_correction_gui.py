import os
from functools import partial
from logging import getLogger
from typing import Callable, Dict, Optional, Tuple

from PyQt5.QtWidgets import QLineEdit

from mantidimaging.core import io
from mantidimaging.core.filters.background_correction import execute
from mantidimaging.core.utility import value_scaling

LOG = getLogger(__name__)


def _gui_register(form, on_change) -> Tuple[Optional[Dict], Optional[Callable], Optional[Callable], Optional[Callable]]:
    from mantidimaging.gui.utility import add_property_to_form

    flat_path_widget, _ = add_property_to_form("Flat", "file", form=form, on_change=on_change)

    dark_path_widget, _ = add_property_to_form("Dark", "file", form=form, on_change=on_change)

    def execute_wrapper() -> partial:
        flat = get_average_image(flat_path_widget)
        dark = get_average_image(dark_path_widget)
        # this will be put in the 'sample' attribute, because we load a single volume
        par = partial(execute, flat=flat, dark=dark)

        return par

    def get_average_image(text_widget: QLineEdit):
        text = str(text_widget.text())
        prefix = io.utility.get_prefix(text)
        extension = io.utility.get_file_extension(text)
        directory = os.path.dirname(text)

        LOG.debug(f"Loading image from widget text: '{text}', directory: '{directory}', "
                  f"prefix: '{prefix}', extension: '{extension}'")
        images_flat_only = io.loader.load(directory, prefix, extension)
        # this will be put in the 'sample' attribute, because we load a single
        # volume
        flat = images_flat_only.sample.mean(axis=0)
        return flat

    def do_before() -> partial:
        return partial(value_scaling.create_factors)

    def do_after() -> partial:
        return partial(value_scaling.apply_factor)

    return None, do_before, execute_wrapper, do_after
