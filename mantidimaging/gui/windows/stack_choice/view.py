from PyQt5 import QtCore
from PyQt5.QtWidgets import QDockWidget, QFrame, QSizePolicy

from mantidimaging.gui.widgets.pg_image_view import MIImageView

from mantidimaging.gui.mvp_base import BaseMainWindowView


class StackChoiceView(BaseMainWindowView):
    def __init__(self, original_stack, new_stack):
        super(StackChoiceView, self).__init__(None, "gui/ui/stack_choice_window.ui")

        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.setWindowTitle("Choose the stack you want to keep")

        # Create stacks and place them in the choice window
        self.original_stack = MIImageView()
        self.original_stack.name = "Original Stack"

        self.new_stack = MIImageView()
        self.new_stack.name = "New Stack"

        self._setup_stack_for_view(self.original_stack, original_stack.data)
        self._setup_stack_for_view(self.new_stack, new_stack.data)

        self.topHorizontalLayout.insertWidget(0, self.original_stack)
        self.topHorizontalLayout.addWidget(self.new_stack)

    def _setup_stack_for_view(self, stack, data):
        stack.setContentsMargins(4, 4, 4, 4)
        stack.setImage(data)
        stack.ui.menuBtn.hide()
        stack.ui.roiBtn.hide()
        stack.button_stack_right.hide()
        stack.button_stack_left.hide()
        self.roiButton.clicked.connect(stack.roiClicked)
