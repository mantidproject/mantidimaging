from functools import partial

from PyQt5 import Qt

from mantidimaging.core.algorithms import gui_compile_ui as gcu
from mantidimaging.gui.algorithm_dialog import AlgorithmDialog, Parameters

from .roi_normalisation import execute

GUI_MENU_NAME = 'ROI Normalisation'


def _gui_register(main_window):
    dialog = AlgorithmDialog(main_window)
    gcu.execute("gui/ui/alg_dialog.ui", dialog)
    dialog.setWindowTitle(GUI_MENU_NAME)

    # TODO add label that from image will be used if nothing is selected here
    label_roi_left = Qt.QLabel("Left")
    roi_left_field = Qt.QSpinBox()
    roi_left_field.setMinimum(0)
    roi_left_field.setMaximum(1000000)

    label_roi_top = Qt.QLabel("Top")
    roi_top_field = Qt.QSpinBox()
    roi_top_field.setMinimum(0)
    roi_top_field.setMaximum(1000000)

    label_roi_right = Qt.QLabel("Right")
    roi_right_field = Qt.QSpinBox()
    roi_right_field.setMinimum(0)
    roi_right_field.setMaximum(1000000)

    label_roi_bottom = Qt.QLabel("Bottom")
    roi_bottom_field = Qt.QSpinBox()
    roi_bottom_field.setMinimum(0)
    roi_bottom_field.setMaximum(1000000)

    dialog.formLayout.addRow(label_roi_left, roi_left_field)
    dialog.formLayout.addRow(label_roi_top, roi_top_field)
    dialog.formLayout.addRow(label_roi_right, roi_right_field)
    dialog.formLayout.addRow(label_roi_bottom, roi_bottom_field)

    def custom_execute():
        roi_left = roi_left_field.value()
        roi_top = roi_top_field.value()
        roi_right = roi_right_field.value()
        roi_bottom = roi_bottom_field.value()
        if roi_left == 0 and roi_top == 0 and roi_right == 0 and roi_bottom == 0:
            dialog.request_parameter(Parameters.ROI)
            return execute
        else:
            air_region = (roi_left, roi_top, roi_right, roi_bottom)
            partial(execute, air_region=air_region)

    dialog.set_execute(custom_execute)
    return dialog
