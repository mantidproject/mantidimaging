# Copyright (C) 2022 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from typing import TYPE_CHECKING

from mantidimaging.gui.mvp_base import BaseMainWindowView
from mantidimaging.gui.widgets.dataset_selector import DatasetSelectorWidgetView

if TYPE_CHECKING:
    from mantidimaging.gui.windows.main import MainWindowView  # noqa:F401  # pragma: no cover


class SpectrumViewerWindowView(BaseMainWindowView):
    sampleStackSelector: DatasetSelectorWidgetView
    flatStackSelector: DatasetSelectorWidgetView

    def __init__(self, main_window: 'MainWindowView'):
        super().__init__(main_window, 'gui/ui/spectrum_viewer.ui')

        self.main_window = main_window

        self._configure_dropdown(self.sampleStackSelector)
        self._configure_dropdown(self.flatStackSelector)

        self.sampleStackSelector.select_eligible_stack()
        self.flatStackSelector.try_to_select_relevant_stack("Flat")

    def cleanup(self):
        self.sampleStackSelector.unsubscribe_from_main_window()
        self.flatStackSelector.unsubscribe_from_main_window()
        self.main_window.spectrum_viewer = None

    def _configure_dropdown(self, selector: DatasetSelectorWidgetView):
        selector.presenter.show_stacks = True
        selector.subscribe_to_main_window(self.main_window)
