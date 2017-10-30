from functools import partial

from . import execute, NAME


def _gui_register(main_window):
    from mantidimaging.gui.algorithm_dialog import AlgorithmDialog

    dialog = AlgorithmDialog(main_window)
    dialog.setWindowTitle(NAME)

    _, rotation_count = dialog.add_property(
            'Number of rotations', 'int', 1, (0, 99))

    def custom_execute():
        num_rotations = rotation_count.value()
        return partial(execute, rotation=num_rotations)

    dialog.set_execute(custom_execute)

    return dialog
