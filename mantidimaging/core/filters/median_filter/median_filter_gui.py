from functools import partial

from . import execute, modes, NAME


def _gui_register(main_window):
    from mantidimaging.gui.algorithm_dialog import AlgorithmDialog

    dialog = AlgorithmDialog(main_window)
    dialog.setWindowTitle(NAME)

    _, size_field = dialog.add_property('Kernel Size', 'int', 3, (0, 1000))

    _, mode_field = dialog.add_property(
            'Mode', 'list', valid_values=modes())

    def custom_execute():
        return partial(execute,
                       size=size_field.value(),
                       mode=mode_field.currentText())

    dialog.set_execute(custom_execute)

    return dialog
