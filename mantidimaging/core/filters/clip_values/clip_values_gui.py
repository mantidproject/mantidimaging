from __future__ import absolute_import, division, print_function

from functools import partial

from PyQt5 import Qt

from mantidimaging.core.algorithms import gui_compile_ui as gcu
from mantidimaging.gui.algorithm_dialog import AlgorithmDialog

from . import clip_values

GUI_MENU_NAME = 'Clip Values'


def _gui_register(main_window):
    dialog = AlgorithmDialog(main_window)
    gcu.execute("gui/ui/alg_dialog.ui", dialog)
    dialog.setWindowTitle(GUI_MENU_NAME)

    label_clip_min = Qt.QLabel("Clip Min")
    label_clip_max = Qt.QLabel("Clip Max")
    clip_min_field = Qt.QDoubleSpinBox()
    clip_min_field.setDecimals(7)
    clip_min_field.setMinimum(-10000000)
    clip_min_field.setMaximum(10000000)

    clip_max_field = Qt.QDoubleSpinBox()
    clip_max_field.setDecimals(7)
    clip_max_field.setMinimum(-10000000)
    clip_max_field.setMaximum(10000000)

    dialog.formLayout.addRow(label_clip_min, clip_min_field)
    dialog.formLayout.addRow(label_clip_max, clip_max_field)

    def custom_execute():
        clip_min = clip_min_field.value()
        clip_max = clip_max_field.value()
        return partial(clip_values.execute, clip_min=clip_min, clip_max=clip_max)

    # replace dialog function with this one
    dialog.set_execute(custom_execute)
    return dialog
