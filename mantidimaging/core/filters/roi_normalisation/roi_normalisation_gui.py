from functools import partial

from mantidimaging.gui.algorithm_dialog import AlgorithmDialog, Parameters

from .roi_normalisation import execute

GUI_MENU_NAME = 'ROI Normalisation'


def _gui_register(main_window):
    dialog = AlgorithmDialog(main_window)
    dialog.setWindowTitle(GUI_MENU_NAME)

    # TODO add label that from image will be used if nothing is selected here

    value_range = (0, 1000000)

    _, roi_left_field = dialog.add_property(
            'Left', 'int', valid_values=value_range)

    _, roi_top_field = dialog.add_property(
            'Top', 'int', valid_values=value_range)

    _, roi_right_field = dialog.add_property(
            'Right', 'int', valid_values=value_range)

    _, roi_bottom_field = dialog.add_property(
            'Bottom', 'int', valid_values=value_range)

    def custom_execute():
        roi_left = roi_left_field.value()
        roi_top = roi_top_field.value()
        roi_right = roi_right_field.value()
        roi_bottom = roi_bottom_field.value()

        if roi_left == 0 and roi_top == 0 and \
                roi_right == 0 and roi_bottom == 0:
            dialog.request_parameter(Parameters.ROI)
            return execute
        else:
            air_region = (roi_left, roi_top, roi_right, roi_bottom)
            partial(execute, air_region=air_region)

    dialog.set_execute(custom_execute)

    return dialog
