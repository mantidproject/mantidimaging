# Copyright (C) 2022 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from typing import TYPE_CHECKING, Optional

from mantidimaging.core.data.dataset import StrictDataset
from mantidimaging.gui.mvp_base import BaseMainWindowView
from mantidimaging.gui.widgets.dataset_selector import DatasetSelectorWidgetView

if TYPE_CHECKING:
    from mantidimaging.gui.windows.main import MainWindowView  # noqa:F401  # pragma: no cover
    from uuid import UUID


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

        self._current_dataset_id = self.main_window.get_dataset_id_from_stack_uuid(self.sampleStackSelector.current())
        self.sampleStackSelector.stack_selected_uuid.connect(self._handle_sample_change)

    def cleanup(self):
        self.sampleStackSelector.unsubscribe_from_main_window()
        self.flatStackSelector.unsubscribe_from_main_window()
        self.main_window.spectrum_viewer = None

    def _configure_dropdown(self, selector: DatasetSelectorWidgetView):
        selector.presenter.show_stacks = True
        selector.subscribe_to_main_window(self.main_window)

    def _handle_sample_change(self, uuid: Optional['UUID']):
        if uuid is None:
            self._current_dataset_id = None
            return

        new_dataset_id = self.main_window.get_dataset_id_from_stack_uuid(uuid)
        if self._current_dataset_id != new_dataset_id:
            self._current_dataset_id = new_dataset_id

            new_dataset = self.main_window.get_dataset(new_dataset_id)
            if isinstance(new_dataset, StrictDataset):
                if new_dataset.flat_before is not None:
                    self.flatStackSelector.try_to_select_relevant_stack(new_dataset.flat_before.name)
                elif new_dataset.flat_after is not None:
                    self.flatStackSelector.try_to_select_relevant_stack(new_dataset.flat_after.name)
