from functools import partial

from PyQt5 import Qt

from isis_imaging.core.algorithms import gui_compile_ui as gcu
from isis_imaging.gui.algorithm_dialog import AlgorithmDialog

from . import median_filter

GUI_MENU_NAME = "Median Filter"


def _gui_register(main_window):
    dialog = AlgorithmDialog(main_window)
    gcu.execute("gui/ui/alg_dialog.ui", dialog)
    dialog.setWindowTitle(GUI_MENU_NAME)

    label_size = Qt.QLabel("Kernel Size")
    size_field = Qt.QSpinBox()
    size_field.setMinimum(0)
    size_field.setMaximum(1000)
    size_field.setValue(3)

    label_mode = Qt.QLabel("Mode")
    mode_field = Qt.QComboBox()
    mode_field.addItems(median_filter.modes())

    dialog.formLayout.addRow(label_size, size_field)
    dialog.formLayout.addRow(label_mode, mode_field)

    def custom_execute():
        return partial(
            median_filter.execute, size=size_field.value(), mode=mode_field.currentText())

    # replace dialog function with this one
    dialog.set_execute(custom_execute)
    return dialog
