from __future__ import absolute_import, division, print_function

import os
from functools import partial

from mantidimaging.core import io
from mantidimaging.core.utility import value_scaling

from . import execute, NAME


def _gui_register(main_window):
    from mantidimaging.gui.algorithm_dialog import AlgorithmDialog

    dialog = AlgorithmDialog(main_window)
    dialog.setWindowTitle(NAME)

    flatPath, _ = dialog.add_property('Flat', 'file')
    darkPath, _ = dialog.add_property('Dark', 'file')

    def custom_execute():
        flat_path = str(flatPath.text())
        dark_path = str(darkPath.text())
        flat_extension = io.utility.get_file_extension(flat_path)
        dark_extension = io.utility.get_file_extension(dark_path)

        flat_dir = os.path.dirname(flat_path)
        dark_dir = os.path.dirname(dark_path)

        images_flat_only = io.loader.load(flat_dir, in_format=flat_extension)

        # this will be put in the 'sample' attribute, because we load a single
        # volume
        flat = images_flat_only.get_sample().mean(axis=0)

        images_dark_only = io.loader.load(dark_dir, in_format=dark_extension)

        # this will be put in the 'sample' attribute, because we load a single
        # volume
        dark = images_dark_only.get_sample().mean(axis=0)

        par = partial(execute, flat=flat, dark=dark)

        return par

    dialog.apply_before(value_scaling.create_factors)

    dialog.apply_after(value_scaling.apply_factor)

    dialog.set_execute(custom_execute)

    return dialog
