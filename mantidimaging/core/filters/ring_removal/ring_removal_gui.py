from functools import partial

from mantidimaging.gui.algorithm_dialog import AlgorithmDialog

from .ring_removal import execute

GUI_MENU_NAME = "Ring Removal"


def _gui_register(main_window):
    dialog = AlgorithmDialog(main_window)
    dialog.setWindowTitle(GUI_MENU_NAME)

    range1 = (0, 1000000)
    range2 = (-1000000, 1000000)

    _, x_field = dialog.add_property('Abcissa X', 'int', valid_values=range1)
    _, y_field = dialog.add_property('Ordinate Y', 'int', valid_values=range1)

    _, thresh = dialog.add_property('Threshold', 'float', valid_values=range2)

    _, thresh_min = dialog.add_property(
            'Threshold Min', 'float', valid_values=range2)

    _, thresh_max = dialog.add_property(
            'Threshold Max', 'float', valid_values=range2)

    _, theta = dialog.add_property('Theta', 'int', valid_values=(-1000, 1000))

    _, rwidth = dialog.add_property('RWidth', 'int', valid_values=range2)

    def custom_execute():
        return partial(execute,
                       run_ring_removal=True,
                       center_x=x_field,
                       center_y=y_field,
                       thresh=thresh,
                       thresh_max=thresh_max,
                       thresh_min=thresh_min,
                       theta_min=theta,
                       rwidth=rwidth)

    dialog.set_execute(custom_execute)

    return dialog
