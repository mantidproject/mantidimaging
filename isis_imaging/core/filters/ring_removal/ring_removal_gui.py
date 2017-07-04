from PyQt5 import Qt
from isis_imaging.core.algorithms import gui_compile_ui as gcu
from isis_imaging.gui.algorithm_dialog import AlgorithmDialog

GUI_MENU_NAME = "Ring Removal"


def _gui_register(main_window):
    dialog = AlgorithmDialog(main_window)
    gcu.execute("gui/ui/alg_dialog.ui", dialog)
    dialog.setWindowTitle(GUI_MENU_NAME)

    label_x = Qt.QLabel("Abcissa X")
    x_field = Qt.QSpinBox()
    x_field.setMinimum(0)
    x_field.setMaximum(1000000)

    label_y = Qt.QLabel("Ordinate Y")
    y_field = Qt.QSpinBox()
    y_field.setMinimum(0)
    y_field.setMaximum(1000000)

    label_thresh = Qt.QLabel("Threshold")
    thresh = Qt.QDoubleSpinBox()
    thresh.setMinimum(-1000000)
    thresh.setMaximum(1000000)

    label_thresh_min = Qt.QLabel("Threshold Min")
    thresh_min = Qt.QDoubleSpinBox()
    thresh_min.setMinimum(-1000000)
    thresh_min.setMaximum(1000000)

    label_thresh_max = Qt.QLabel("Threshold Max")
    thresh_max = Qt.QDoubleSpinBox()
    thresh_max.setMinimum(-1000000)
    thresh_max.setMaximum(1000000)

    label_theta = Qt.QLabel("Theta")
    theta = Qt.QSpinBox()
    theta.setMinimum(-1000)
    theta.setMaximum(1000)

    label_rwidth = Qt.QLabel("RWidth")
    rwidth = Qt.QSpinBox()
    rwidth.setMinimum(-1000000)
    rwidth.setMaximum(1000000)

    dialog.formLayout.addRow(label_x, x_field)
    dialog.formLayout.addRow(label_y, y_field)
    dialog.formLayout.addRow(label_thresh, thresh)
    dialog.formLayout.addRow(label_thresh_min, thresh_min)
    dialog.formLayout.addRow(label_thresh_max, thresh_max)
    dialog.formLayout.addRow(label_theta, theta)
    dialog.formLayout.addRow(label_rwidth, rwidth)

    def decorate_execute():
        from functools import partial
        return partial(
            execute,
            center_x=x_field,
            center_y=y_field,
            thresh=thresh,
            thresh_max=thresh_max,
            thresh_min=thresh_min,
            theta_min=theta,
            rwidth=rwidth)

    # replace dialog function with this one
    dialog.decorate_execute = decorate_execute
    return dialog