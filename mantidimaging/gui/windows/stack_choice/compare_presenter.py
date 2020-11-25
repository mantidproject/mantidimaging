# Copyright (C) 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later

import traceback

from mantidimaging.core.data.images import Images
from mantidimaging.gui.windows.stack_choice.presenter_base import StackChoicePresenterMixin
from mantidimaging.gui.windows.stack_choice.view import StackChoiceView


class StackComparePresenter(StackChoicePresenterMixin):
    def __init__(self, stack_one: Images, stack_two: Images, parent):
        self.view = StackChoiceView(stack_one, stack_two, self, parent)
        self.view.originalDataButton.hide()
        self.view.newDataButton.hide()

        # forces the view's closeEvent to not prompt any dialogs, but only free the image views
        self.view.choice_made = True
        self.view.setWindowTitle("Comparing data")

    def show(self):
        self.view.show()

    def notify(self, signal):
        try:
            super().notify(signal)
        except Exception as e:
            self.show_error(e, traceback.format_exc())
