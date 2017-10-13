from functools import partial

from mantidimaging.gui.algorithm_dialog import AlgorithmDialog

from . import rotate_stack

GUI_MENU_NAME = 'Rotate Stack'


def _gui_register(main_window):
    dialog = AlgorithmDialog(main_window)
    dialog.setWindowTitle(GUI_MENU_NAME)

    _, rotation_count = dialog.add_property(
            'Number of rotations', 'int', 1, (0, 99))

    def custom_execute():
        num_rotations = rotation_count.value()
        return partial(rotate_stack.execute, rotation=num_rotations)

    dialog.set_execute(custom_execute)

    return dialog
