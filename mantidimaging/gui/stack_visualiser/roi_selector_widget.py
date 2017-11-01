from __future__ import absolute_import, division, print_function

from PyQt5 import Qt

from mantidimaging.core.utility import gui_compile_ui

from .presenter import Notification


class ROISelectorWidget(Qt.QWidget):

    def __init__(self, parent, stack_view):
        super(ROISelectorWidget, self).__init__(parent)
        gui_compile_ui.execute('gui/ui/roi_selector_widget.ui', self)

        self.stack_view = stack_view

        self.image_size = (1, 1)

        self.leftRoiBound.valueChanged[int].connect(self.on_user_changes_roi)
        self.topRoiBound.valueChanged[int].connect(self.on_user_changes_roi)
        self.rightRoiBound.valueChanged[int].connect(self.on_user_changes_roi)
        self.bottomRoiBound.valueChanged[int].connect(self.on_user_changes_roi)

        self.clearRoiButton.clicked.connect(
                lambda: self.stack_view.presenter.notify(Notification.CLEAR_ROI))

    @property
    def image_size(self):
        return [
            self.rightRoiBound.maximum(),
            self.bottomRoiBound.maximum()
        ]

    @image_size.setter
    def image_size(self, size):
        if len(size) != 2:
            return

        self.rightRoiBound.setMaximum(size[0])
        self.bottomRoiBound.setMaximum(size[1])

    @property
    def roi(self):
        return [
            self.leftRoiBound.value(),
            self.topRoiBound.value(),
            self.rightRoiBound.value(),
            self.bottomRoiBound.value()
        ]

    @roi.setter
    def roi(self, roi):
        if len(roi) != 4:
            return

        self.leftRoiBound.setValue(roi[0])
        self.rightRoiBound.setValue(roi[1])
        self.topRoiBound.setValue(roi[2])
        self.bottomRoiBound.setValue(roi[3])

        self.validate_roi()

    def validate_roi(self):
        """
        Checks if the ROI bounds are in the correct order and swaps pairs of
        bounds if they are not.
        """
        roi = self.roi

        def check_and_swap(idx_low, idx_high):
            if roi[idx_low] > roi[idx_high]:
                roi[idx_low], roi[idx_high] = roi[idx_high], roi[idx_low]
                return True
            return False

        if check_and_swap(0, 2) or check_and_swap(1, 3):
            self.roi = roi

    def on_user_changes_roi(self, _):
        """
        Called when the user changes the ROI via one of the spin boxes on this
        widget.
        """
        self.validate_roi()

        roi = self.roi
        print(roi)
