from functools import partial

from . import execute, NAME


def _gui_register(main_window):
    from mantidimaging.gui.algorithm_dialog import AlgorithmDialog

    dialog = AlgorithmDialog(main_window)
    dialog.setWindowTitle(NAME)

    _, threshold_field = dialog.add_property(
            'Threshold', 'float', 0.95, (0.0, 1.0))
    threshold_field.setSingleStep(0.05)

    def custom_execute():
        return partial(execute, threshold=threshold_field.value())

    dialog.set_execute(custom_execute)

    return dialog
