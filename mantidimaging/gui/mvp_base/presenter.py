# Copyright (C) 2024 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

from logging import getLogger
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mantidimaging.gui.mvp_base import BaseMainWindowView, BaseDialogView  # pragma: no cover


class BasePresenter(object):
    view: 'BaseMainWindowView' | 'BaseDialogView'

    def __init__(self, view: 'BaseMainWindowView'):
        self.view = view

    def notify(self, signal):
        raise NotImplementedError("Presenter must implement the notify() method")

    def show_error(self, error, traceback):
        getLogger(__name__).exception(f'Presenter error: {error}\n{traceback}')
        if hasattr(self.view, 'show_error_dialog'):
            # If the view knows how to handle an error message
            self.view.show_error_dialog(str(error))

    def show_information(self, info):
        self.view.show_info_dialog(info)
