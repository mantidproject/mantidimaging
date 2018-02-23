from PyQt5 import Qt

from mantidimaging.gui.utility import (BlockQtSignals, compile_ui)

from .presenter import Notification


def validate_and_swap_roi_values(roi):
    roi = list(roi)

    def check_and_swap(idx_low, idx_high):
        if roi[idx_low] > roi[idx_high]:
            roi[idx_low], roi[idx_high] = roi[idx_high], roi[idx_low]
            return True
        return False

    result = check_and_swap(0, 2) or check_and_swap(1, 3)

    return result, tuple(roi)


class ROISelectorWidget(Qt.QWidget):

    def __init__(self, parent, stack_view):
        super(ROISelectorWidget, self).__init__(parent)
        compile_ui('gui/ui/roi_selector_widget.ui', self)

        self.stack_view = stack_view

        self.image_size = (1, 1)

        self.leftRoiBound.valueChanged[int].connect(self.on_user_changes_roi)
        self.topRoiBound.valueChanged[int].connect(self.on_user_changes_roi)
        self.rightRoiBound.valueChanged[int].connect(self.on_user_changes_roi)
        self.bottomRoiBound.valueChanged[int].connect(self.on_user_changes_roi)

        self.clearRoiButton.clicked.connect(
                lambda: self.stack_view.presenter.notify(
                    Notification.CLEAR_ROI))

    @property
    def image_size(self):
        return (
            self.rightRoiBound.maximum(),
            self.bottomRoiBound.maximum()
        )

    @image_size.setter
    def image_size(self, size):
        if len(size) != 2:
            return

        self.leftRoiBound.setMaximum(size[0])
        self.topRoiBound.setMaximum(size[1])
        self.rightRoiBound.setMaximum(size[0])
        self.bottomRoiBound.setMaximum(size[1])

    @property
    def roi(self):
        return (
            self.leftRoiBound.value(),
            self.topRoiBound.value(),
            self.rightRoiBound.value(),
            self.bottomRoiBound.value()
        )

    @roi.setter
    def roi(self, roi):
        if roi is None:
            return

        if len(roi) != 4:
            return

        _, roi = validate_and_swap_roi_values(roi)

        with BlockQtSignals(
                [self.leftRoiBound, self.topRoiBound,
                 self.rightRoiBound, self.bottomRoiBound]):
            self.leftRoiBound.setValue(roi[0])
            self.topRoiBound.setValue(roi[1])
            self.rightRoiBound.setValue(roi[2])
            self.bottomRoiBound.setValue(roi[3])

    def on_user_changes_roi(self, _):
        """
        Called when the user changes the ROI via one of the spin boxes on this
        widget.
        """
        self.stack_view.current_roi = self.roi
