from PyQt5 import Qt

from isis_imaging.core.algorithms import gui_compile_ui as gcu
from isis_imaging.gui.algorithm_dialog import AlgorithmDialog

from . import outliers

GUI_MENU_NAME="Outliers"


def _gui_register(main_window):
    dialog = AlgorithmDialog(main_window)
    gcu.execute("gui/ui/alg_dialog.ui", dialog)
    dialog.setWindowTitle(GUI_MENU_NAME)

    label_diff = Qt.QLabel("Difference")
    diff_field = Qt.QSpinBox()
    diff_field.setMinimum(-1000000)
    diff_field.setMaximum(1000000)
    diff_field.setValue(1)

    label_size = Qt.QLabel("Size")
    size_field = Qt.QSpinBox()
    size_field.setMinimum(0)
    size_field.setMaximum(1000)
    size_field.setValue(3)

    label_mode = Qt.QLabel("Mode")
    mode_field = Qt.QComboBox()
    mode_field.addItems(outliers.modes())

    dialog.formLayout.addRow(label_diff, diff_field)
    dialog.formLayout.addRow(label_size, size_field)
    dialog.formLayout.addRow(label_mode, mode_field)

    def decorate_execute():
        from functools import partial
        return partial(
            outliers.execute,
            diff=diff_field.value(),
            radius=size_field.value(),
            mode=mode_field.currentText())

    # replace dialog function with this one
    dialog.decorate_execute = decorate_execute
    return dialog
