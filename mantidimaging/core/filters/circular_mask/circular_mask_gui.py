from __future__ import absolute_import, division, print_function

from functools import partial

from PyQt5 import Qt

from mantidimaging.core.algorithms import gui_compile_ui as gcu
from mantidimaging.gui.algorithm_dialog import AlgorithmDialog

from . import circular_mask

GUI_MENU_NAME = 'Circular Mask'


def _gui_register(main_window):
    dialog = AlgorithmDialog(main_window)
    gcu.execute("gui/ui/alg_dialog.ui", dialog)
    dialog.setWindowTitle(GUI_MENU_NAME)

    label_radius = Qt.QLabel("Radius")
    radius_field = Qt.QDoubleSpinBox()
    radius_field.setMinimum(0)
    radius_field.setMaximum(1)
    radius_field.setValue(0.95)

    label_value = Qt.QLabel("Set to value")
    value_field = Qt.QDoubleSpinBox()
    value_field.setMinimum(-100000)
    value_field.setMaximum(100000)
    value_field.setValue(0)

    dialog.formLayout.addRow(label_radius, radius_field)
    dialog.formLayout.addRow(label_value, value_field)

    def custom_execute():
        return partial(
            circular_mask.execute,
            circular_mask_ratio=radius_field.value(),
            circular_mask_value=value_field.value())

    # replace dialog function with this one
    dialog.set_execute(custom_execute)
    return dialog
