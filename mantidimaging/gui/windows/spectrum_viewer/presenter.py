# Copyright (C) 2022 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from typing import TYPE_CHECKING, Optional

from mantidimaging.core.data.dataset import StrictDataset
from mantidimaging.gui.mvp_base import BasePresenter

if TYPE_CHECKING:
    from mantidimaging.gui.windows.spectrum_viewer.view import SpectrumViewerWindowView  # pragma: no cover
    from mantidimaging.gui.windows.main.view import MainWindowView  # pragma: no cover
    from uuid import UUID


class SpectrumViewerWindowPresenter(BasePresenter):
    view: 'SpectrumViewerWindowView'

    def __init__(self, view: 'SpectrumViewerWindowView', main_window: 'MainWindowView'):
        super().__init__(view)

        self.view = view
        self.main_window = main_window

    def handle_sample_change(self, uuid: Optional['UUID']) -> None:
        new_dataset_id = self.get_dataset_id_for_stack(uuid)
        if new_dataset_id is None:
            self.view.current_dataset_id = None
            return

        if self.view.current_dataset_id != new_dataset_id:
            self.view.current_dataset_id = new_dataset_id

            new_dataset = self.main_window.get_dataset(new_dataset_id)
            if isinstance(new_dataset, StrictDataset):
                if new_dataset.flat_before is not None:
                    self.view.try_to_select_relevant_normalise_stack(new_dataset.flat_before.name)
                elif new_dataset.flat_after is not None:
                    self.view.try_to_select_relevant_normalise_stack(new_dataset.flat_after.name)

        if uuid is not None:
            self.show_new_sample(uuid)

    def get_dataset_id_for_stack(self, stack_id: Optional['UUID']) -> Optional['UUID']:
        return None if stack_id is None else self.main_window.get_dataset_id_from_stack_uuid(stack_id)

    def show_new_sample(self, uuid: 'UUID'):
        stack = self.main_window.get_stack(uuid)

        stack_averaged = stack.data.mean(axis=0)
        stack_spectrum = stack.data.mean(axis=(1, 2))

        self.view.spectrum.image.setImage(stack_averaged)
        self.view.spectrum.spectrum.plot(stack_spectrum, clear=True)
