from functools import partial

from . import execute, NAME


def _gui_register(main_window):
    from mantidimaging.gui.algorithm_dialog import AlgorithmDialog

    dialog = AlgorithmDialog(main_window)
    dialog.setWindowTitle(NAME)

    # Not much here, this filter does one thing and one thing only.

    def custom_execute():
        return partial(execute, minus_log=True)

    dialog.set_execute(custom_execute)

    return dialog
