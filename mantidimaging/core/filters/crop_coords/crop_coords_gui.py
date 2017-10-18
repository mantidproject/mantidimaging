from __future__ import absolute_import, division, print_function

from functools import partial

from . import crop_coords, NAME


def _gui_register(main_window):
    from mantidimaging.gui.algorithm_dialog import AlgorithmDialog

    dialog = AlgorithmDialog(main_window)
    dialog.setWindowTitle(NAME)

    valid_range = (0, 99999)

    _, left = dialog.add_property('Left', 'int', valid_values=valid_range)
    _, top = dialog.add_property('Top', 'int', valid_values=valid_range)
    _, right = dialog.add_property('Right', 'int', valid_values=valid_range)
    _, bottom = dialog.add_property('Bottom', 'int', valid_values=valid_range)

    def custom_execute():
        # Get ROI from input fields
        roi = [left.value(), top.value(), right.value(), bottom.value()]

        return partial(crop_coords._execute, region_of_interest=roi)

    dialog.set_execute(custom_execute)

    return dialog
