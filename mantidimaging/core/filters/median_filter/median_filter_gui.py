from functools import partial

from mantidimaging.gui.algorithm_dialog import AlgorithmDialog

from . import median_filter

GUI_MENU_NAME = "Median Filter"


def _gui_register(main_window):
    dialog = AlgorithmDialog(main_window)
    dialog.setWindowTitle(GUI_MENU_NAME)

    _, size_field = dialog.add_property('Kernel Size', 'int', 3, (0, 1000))

    _, mode_field = dialog.add_property(
            'Mode', 'list', valid_values=median_filter.modes())

    def custom_execute():
        return partial(median_filter.execute,
                       size=size_field.value(), mode=mode_field.currentText())

    dialog.set_execute(custom_execute)

    return dialog
