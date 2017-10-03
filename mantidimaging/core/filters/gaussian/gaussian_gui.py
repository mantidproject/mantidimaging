from functools import partial

from mantidimaging.gui.algorithm_dialog import AlgorithmDialog

from . import gaussian

GUI_MENU_NAME = "Gaussian Filter"


def _gui_register(main_window):
    dialog = AlgorithmDialog(main_window)
    dialog.setWindowTitle(GUI_MENU_NAME)

    _, size_field = dialog.add_property('Kernel Size', 'int', 3, (0, 1000))

    _, order_field = dialog.add_property('Order', 'int', 0, (0, 3))

    _, mode_field = dialog.add_property(
            'Mode', 'list', valid_values=gaussian.modes())

    def custom_execute():
        return partial(
            gaussian.execute,
            size=size_field.value(),
            mode=mode_field.currentText(),
            order=order_field.value())

    dialog.set_execute(custom_execute)

    return dialog
