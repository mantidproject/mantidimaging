# Copyright (C) 2022 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later

import traceback

from mantidimaging.core.data.imagestack import ImageStack
from mantidimaging.gui.windows.stack_choice.presenter_base import StackChoicePresenterMixin
from mantidimaging.gui.windows.stack_choice.view import StackChoiceView


class StackComparePresenter(StackChoicePresenterMixin):
    def __init__(self, stack_one: ImageStack, stack_two: ImageStack, parent):
        self.view = StackChoiceView(stack_one, stack_two, self, parent)
        self.view.originalDataButton.hide()
        self.view.newDataButton.hide()

        # forces the view's closeEvent to not prompt any dialogs, but only free the image views
        self.view.choice_made = True
        self.view.setWindowTitle("Comparing data")

        stack_one_name = parent.find_images_stack_title(stack_one)
        stack_two_name = parent.find_images_stack_title(stack_two)
        self.view.originalStackLabel.setText(stack_one_name)
        self.view.newStackLabel.setText(stack_two_name)

    def show(self):
        self.view.show()

    def notify(self, signal):
        try:
            super().notify(signal)
        except Exception as e:
            self.show_error(e, traceback.format_exc())
