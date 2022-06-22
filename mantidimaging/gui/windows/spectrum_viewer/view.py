# Copyright (C) 2022 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from typing import TYPE_CHECKING, Optional

from PyQt5.QtWidgets import QCheckBox, QVBoxLayout

from mantidimaging.gui.mvp_base import BaseMainWindowView
from mantidimaging.gui.widgets.dataset_selector import DatasetSelectorWidgetView
from .presenter import SpectrumViewerWindowPresenter
from .spectrum_widget import SpectrumWidget

if TYPE_CHECKING:
    from mantidimaging.gui.windows.main import MainWindowView  # noqa:F401  # pragma: no cover
    from uuid import UUID


class SpectrumViewerWindowView(BaseMainWindowView):
    sampleStackSelector: DatasetSelectorWidgetView
    normaliseStackSelector: DatasetSelectorWidgetView

    normaliseCheckBox: QCheckBox
    imageLayout: QVBoxLayout

    def __init__(self, main_window: 'MainWindowView'):
        super().__init__(main_window, 'gui/ui/spectrum_viewer.ui')

        self.main_window = main_window
        self.presenter = SpectrumViewerWindowPresenter(self, main_window)

        self._configure_dropdown(self.sampleStackSelector)
        self._configure_dropdown(self.normaliseStackSelector)

        self.sampleStackSelector.select_eligible_stack()
        self.try_to_select_relevant_normalise_stack("Flat")

        self._current_dataset_id = self.presenter.get_dataset_id_for_stack(self.sampleStackSelector.current())
        self.sampleStackSelector.stack_selected_uuid.connect(self.presenter.handle_sample_change)
        self.normaliseCheckBox.stateChanged.connect(self.set_normalise_dropdown_state)

        self.spectrum = SpectrumWidget(self)
        self.imageLayout.addWidget(self.spectrum)

    def cleanup(self):
        self.sampleStackSelector.unsubscribe_from_main_window()
        self.normaliseStackSelector.unsubscribe_from_main_window()
        self.main_window.spectrum_viewer = None

    @property
    def current_dataset_id(self) -> Optional['UUID']:
        return self._current_dataset_id

    @current_dataset_id.setter
    def current_dataset_id(self, uuid: Optional['UUID']) -> None:
        self._current_dataset_id = uuid

    def _configure_dropdown(self, selector: DatasetSelectorWidgetView) -> None:
        selector.presenter.show_stacks = True
        selector.subscribe_to_main_window(self.main_window)

    def set_normalise_dropdown_state(self) -> None:
        if self.normaliseCheckBox.isChecked():
            self.normaliseStackSelector.setEnabled(True)
        else:
            self.normaliseStackSelector.setEnabled(False)

    def try_to_select_relevant_normalise_stack(self, name: str) -> None:
        self.normaliseStackSelector.try_to_select_relevant_stack(name)
