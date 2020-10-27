from enum import Enum, auto

from PyQt5 import QtCore
from PyQt5.QtWidgets import QSizePolicy, QMessageBox

from mantidimaging.gui.widgets.pg_image_view import MIImageView

from mantidimaging.gui.mvp_base import BaseMainWindowView


class Notification(Enum):
    CHOOSE_ORIGINAL = auto()
    CHOOSE_NEW_DATA = auto()


class StackChoiceView(BaseMainWindowView):
    def __init__(self, original_stack, new_stack, presenter):
        super(StackChoiceView, self).__init__(None, "gui/ui/stack_choice_window.ui")

        self.presenter = presenter

        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.setWindowTitle("Choose the stack you want to keep")

        # Create stacks and place them in the choice window
        self.original_stack = MIImageView(detailsSpanAllCols=True)
        self.original_stack.name = "Original Stack"

        self.new_stack = MIImageView(detailsSpanAllCols=True)
        self.new_stack.name = "New Stack"

        self._setup_stack_for_view(self.original_stack, original_stack.data)
        self._setup_stack_for_view(self.new_stack, new_stack.data)

        self.topHorizontalLayout.insertWidget(0, self.original_stack)
        self.topHorizontalLayout.addWidget(self.new_stack)

        self.shifting_through_images = False
        self.original_stack.sigTimeChanged.connect(self._sync_new_stack_with_old_stack)
        self.new_stack.sigTimeChanged.connect(self._sync_old_stack_with_new_stack)

        # Hook nav buttons into original stack (new stack not needed as the timelines are synced)
        self.leftButton.pressed.connect(self.original_stack.button_stack_left.pressed)
        self.leftButton.released.connect(self.original_stack.button_stack_left.released)
        self.rightButton.pressed.connect(self.original_stack.button_stack_right.pressed)
        self.rightButton.released.connect(self.original_stack.button_stack_right.released)

    def _setup_stack_for_view(self, stack, data):
        stack.setContentsMargins(4, 4, 4, 4)
        stack.setImage(data)
        stack.ui.menuBtn.hide()
        stack.ui.roiBtn.hide()
        stack.button_stack_right.hide()
        stack.button_stack_left.hide()
        details_size_policy = QSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Preferred)
        details_size_policy.setHorizontalStretch(1)
        stack.details.setSizePolicy(details_size_policy)
        self.roiButton.clicked.connect(stack.roiClicked)

    def _sync_new_stack_with_old_stack(self, index, _):
        self.new_stack.sigTimeChanged.disconnect(self._sync_old_stack_with_new_stack)
        self.new_stack.setCurrentIndex(index)
        self.new_stack.sigTimeChanged.connect(self._sync_old_stack_with_new_stack)

    def _sync_old_stack_with_new_stack(self, index, _):
        self.original_stack.sigTimeChanged.disconnect(self._sync_new_stack_with_old_stack)
        self.original_stack.setCurrentIndex(index)
        self.original_stack.sigTimeChanged.connect(self._sync_new_stack_with_old_stack)

    def closeEvent(self, e):
        # Confirm exit is actually wanted as it will lead to data loss
        response = QMessageBox.Warning(self, "Data Loss! Are you sure?",
                                       "You will lose the original stack if you close this window! Are you sure?",
                                       QMessageBox.Ok | QMessageBox.Cancel)
        if response == QMessageBox.Ok:
            self.presenter.notify(Notification.CHOOSE_NEW_DATA)
