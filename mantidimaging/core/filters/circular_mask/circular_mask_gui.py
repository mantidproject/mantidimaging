from __future__ import absolute_import, division, print_function

from functools import partial

from mantidimaging.gui.algorithm_dialog import AlgorithmDialog

from . import circular_mask

GUI_MENU_NAME = 'Circular Mask'


def _gui_register(main_window):
    dialog = AlgorithmDialog(main_window)
    dialog.setWindowTitle(GUI_MENU_NAME)

    _, radius_field = dialog.add_property('Radius', 'float', 0.95, (0.0, 1.0))

    _, value_field = dialog.add_property(
            'Set to value', 'float', 0, (-10000, 10000))

    def custom_execute():
        return partial(
            circular_mask.execute,
            circular_mask_ratio=radius_field.value(),
            circular_mask_value=value_field.value())

    # replace dialog function with this one
    dialog.set_execute(custom_execute)
    return dialog
