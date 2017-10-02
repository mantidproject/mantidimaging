from functools import partial

from mantidimaging.gui.algorithm_dialog import AlgorithmDialog

from . import cut_off

GUI_MENU_NAME = 'Cut Off'


def _gui_register(main_window):
    dialog = AlgorithmDialog(main_window)
    dialog.setWindowTitle("Cut Off")

    _, threshold_field = dialog.add_property(
            'Threshold', 'float', 0.95, (0.0, 1.0))
    threshold_field.setSingleStep(0.05)

    def custom_execute():
        return partial(cut_off.execute, threshold=threshold_field.value())

    dialog.set_execute(custom_execute)

    return dialog
