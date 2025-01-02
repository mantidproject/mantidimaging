# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

from mantidimaging.gui.mvp_base.presenter import BasePresenter
from mantidimaging.gui.windows.stack_choice.view import Notification


class StackChoicePresenterMixin(BasePresenter):
    """
    Implements common functions for StackChoice and StackCompare, but does
    not do enough on it's own for a successful view initialisation - it needs
    to be mixed into another presenter that extends it
    """

    def notify(self, signal: Notification):
        if signal == Notification.TOGGLE_LOCK_HISTOGRAMS:
            self.do_toggle_lock_histograms()

    def do_toggle_lock_histograms(self):
        # The state of the button changes before this signal is triggered
        # so on first click you get isChecked = True
        histograms_should_lock = self.view.lockHistograms.isChecked()

        if histograms_should_lock:
            self.view.connect_histogram_changes()
        else:
            self.view.disconnect_histogram_changes()
