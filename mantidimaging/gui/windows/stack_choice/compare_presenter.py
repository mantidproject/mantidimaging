# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

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
        self.view.setWindowTitle("Compare Image Stacks")

        self.view.originalStackLabel.setText(stack_one.name)
        self.view.newStackLabel.setText(stack_two.name)

    def show(self) -> None:
        self.view.show()

    def notify(self, signal) -> None:
        try:
            super().notify(signal)
        except Exception as e:
            self.show_error(e, traceback.format_exc())
