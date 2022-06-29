# Copyright (C) 2022 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from typing import TYPE_CHECKING, Optional

from mantidimaging.core.data.dataset import StrictDataset
from mantidimaging.gui.mvp_base import BasePresenter
from mantidimaging.gui.windows.spectrum_viewer.model import SpectrumViewerWindowModel

if TYPE_CHECKING:
    from mantidimaging.gui.windows.spectrum_viewer.view import SpectrumViewerWindowView  # pragma: no cover
    from mantidimaging.gui.windows.main.view import MainWindowView  # pragma: no cover
    from uuid import UUID


class SpectrumViewerWindowPresenter(BasePresenter):
    view: 'SpectrumViewerWindowView'
    model: SpectrumViewerWindowModel

    def __init__(self, view: 'SpectrumViewerWindowView', main_window: 'MainWindowView'):
        super().__init__(view)

        self.view = view
        self.main_window = main_window
        self.model = SpectrumViewerWindowModel(self)

    def handle_sample_change(self, uuid: Optional['UUID']) -> None:
        new_dataset_id = self.get_dataset_id_for_stack(uuid)

        if new_dataset_id:
            self.auto_find_flat_stack(new_dataset_id)
        else:
            self.view.current_dataset_id = None

        if uuid is not None:
            self.model.set_stack(self.main_window.get_stack(uuid))
            normalise_uuid = self.view.get_normalise_stack()
            if normalise_uuid is not None:
                self.model.set_open_stack(self.main_window.get_stack(normalise_uuid))
            self.show_new_sample(uuid)

    def auto_find_flat_stack(self, new_dataset_id):
        if self.view.current_dataset_id != new_dataset_id:
            self.view.current_dataset_id = new_dataset_id

            new_dataset = self.main_window.get_dataset(new_dataset_id)
            if isinstance(new_dataset, StrictDataset):
                if new_dataset.flat_before is not None:
                    self.view.try_to_select_relevant_normalise_stack(new_dataset.flat_before.name)
                elif new_dataset.flat_after is not None:
                    self.view.try_to_select_relevant_normalise_stack(new_dataset.flat_after.name)

    def get_dataset_id_for_stack(self, stack_id: Optional['UUID']) -> Optional['UUID']:
        return None if stack_id is None else self.main_window.get_dataset_id_from_stack_uuid(stack_id)

    def show_new_sample(self, uuid: 'UUID'):
        stack = self.main_window.get_stack(uuid)

        stack_spectrum = stack.data.mean(axis=(1, 2))

        self.view.spectrum.image.setImage(self.model.get_averaged_image())
        self.view.spectrum.spectrum.plot(stack_spectrum, clear=True)
        self.view.spectrum.add_range(*self.model.tof_range)
