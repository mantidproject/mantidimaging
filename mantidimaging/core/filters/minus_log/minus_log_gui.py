from functools import partial

from mantidimaging.gui.algorithm_dialog import AlgorithmDialog

from . import minus_log

GUI_MENU_NAME = "Minus Log"


def _gui_register(main_window):
    dialog = AlgorithmDialog(main_window)
    dialog.setWindowTitle(GUI_MENU_NAME)

    # Not much here, this filter does one thing and one thing only.

    def custom_execute():
        return partial(minus_log.execute, minus_log=True)

    dialog.set_execute(custom_execute)

    return dialog
