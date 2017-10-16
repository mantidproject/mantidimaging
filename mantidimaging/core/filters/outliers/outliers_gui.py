from functools import partial

from . import execute, modes, NAME


def _gui_register(main_window):
    from mantidimaging.gui.algorithm_dialog import AlgorithmDialog

    dialog = AlgorithmDialog(main_window)
    dialog.setWindowTitle(NAME)

    _, diff_field = dialog.add_property(
            'Difference', 'int', 1, (-1000000, 1000000))

    _, size_field = dialog.add_property('Size', 'int', 3, (0, 1000))

    _, mode_field = dialog.add_property(
            'Mode', 'list', valid_values=modes())

    def decorate_execute():
        return partial(execute,
                       diff=diff_field.value(),
                       radius=size_field.value(),
                       mode=mode_field.currentText())

    dialog.set_execute(decorate_execute)

    return dialog
