# Copyright (C) 2023 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

import traceback
from typing import TYPE_CHECKING

from mantidimaging.core.data.imagestack import ImageStack
from mantidimaging.gui.windows.stack_choice.presenter_base import StackChoicePresenterMixin
from mantidimaging.gui.windows.stack_choice.view import Notification, StackChoiceView

if TYPE_CHECKING:
    from mantidimaging.gui.windows.operations.presenter import FiltersWindowPresenter  # pragma: no cover


class StackChoicePresenter(StackChoicePresenterMixin):

    def __init__(self, original_stack: ImageStack, new_stack: ImageStack,
                 operations_presenter: 'FiltersWindowPresenter'):

        self.operations_presenter = operations_presenter
        self.original_stack = original_stack

        self.view = StackChoiceView(self.original_stack, new_stack, self, parent=operations_presenter.view)
        self.new_stack = new_stack
        self.done = False
        self.use_new_data = False

    def show(self):
        self.view.show()

    def notify(self, signal):
        try:
            if signal == Notification.CHOOSE_ORIGINAL:
                self.do_reapply_original_data()
            elif signal == Notification.CHOOSE_NEW_DATA:
                self.do_clean_up_original_data()
                self.use_new_data = True
            else:
                super().notify(signal)
        except Exception as e:
            self.show_error(e, traceback.format_exc())

    def do_reapply_original_data(self):
        self.new_stack.shared_array = self.original_stack.shared_array
        self.new_stack.metadata = self.original_stack.metadata
        self.view.choice_made = True
        self.close_view()

    def do_clean_up_original_data(self):
        self.view.choice_made = True
        self.close_view()

    def close_view(self):
        self.view.close()
        self.original_stack = None
        self.done = True

    def enable_nonpositive_check(self):
        self.view.original_stack.enable_nonpositive_check()
        self.view.new_stack.enable_nonpositive_check()
