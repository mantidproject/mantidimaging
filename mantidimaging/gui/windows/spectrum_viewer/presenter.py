# Copyright (C) 2022 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from typing import TYPE_CHECKING, Optional

from mantidimaging.core.data.dataset import StrictDataset
from mantidimaging.gui.mvp_base import BasePresenter
from mantidimaging.gui.windows.spectrum_viewer.model import SpectrumViewerWindowModel, SpecType

if TYPE_CHECKING:
    from mantidimaging.gui.windows.spectrum_viewer.view import SpectrumViewerWindowView  # pragma: no cover
    from mantidimaging.gui.windows.main.view import MainWindowView  # pragma: no cover
    from mantidimaging.core.data import ImageStack
    from uuid import UUID


class SpectrumViewerWindowPresenter(BasePresenter):
    """
    The presenter for the spectrum viewer window.

    This presenter is responsible for handling user interaction with the view and
    updating the model and view accordingly to look after the state of the window.
    """
    view: 'SpectrumViewerWindowView'
    model: SpectrumViewerWindowModel
    spectrum_mode: SpecType = SpecType.SAMPLE
    current_stack_uuid: Optional['UUID'] = None
    current_norm_stack_uuid: Optional['UUID'] = None

    def __init__(self, view: 'SpectrumViewerWindowView', main_window: 'MainWindowView'):
        super().__init__(view)

        self.view = view
        self.main_window = main_window
        self.model = SpectrumViewerWindowModel(self)

    def handle_sample_change(self, uuid: Optional['UUID']) -> None:
        if uuid == self.current_stack_uuid:
            return
        else:
            self.current_stack_uuid = uuid
        new_dataset_id = self.get_dataset_id_for_stack(uuid)

        if new_dataset_id:
            self.auto_find_flat_stack(new_dataset_id)
        else:
            self.view.current_dataset_id = None

        if uuid is None:
            self.model.set_stack(None)
            self.view.clear()
            self.handle_export_button_enabled()
            return

        self.model.set_stack(self.main_window.get_stack(uuid))
        normalise_uuid = self.view.get_normalise_stack()
        if normalise_uuid is not None:
            try:
                norm_stack: Optional['ImageStack'] = self.main_window.get_stack(normalise_uuid)
            except RuntimeError:
                norm_stack = None
            self.model.set_normalise_stack(norm_stack)

        self.view.set_normalise_error(self.model.normalise_issue())
        self.show_new_sample()
        self.handle_export_button_enabled()

    def handle_normalise_stack_change(self, normalise_uuid: Optional['UUID']) -> None:
        if normalise_uuid == self.current_norm_stack_uuid:
            return
        else:
            self.current_norm_stack_uuid = normalise_uuid

        if normalise_uuid is None:
            self.model.set_normalise_stack(None)
            return

        self.model.set_normalise_stack(self.main_window.get_stack(normalise_uuid))
        self.view.set_normalise_error(self.model.normalise_issue())
        self.handle_roi_moved()

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

    def show_new_sample(self) -> None:
        self.view.set_image(self.model.get_averaged_image())
        self.view.set_spectrum(self.model.get_spectrum("roi", self.spectrum_mode))
        self.view.spectrum.add_range(*self.model.tof_range)
        self.view.spectrum.add_roi(self.model.get_roi("roi"), "roi")
        self.view.auto_range_image()

    def get_default_table_state(self) -> list:
        """
        Get the default state of the table
        """
        return ["roi", self.view.spectrum.roi_dict["roi"].colour]

    def handle_range_slide_moved(self, tof_range) -> None:
        self.model.tof_range = tof_range
        self.view.set_image(self.model.get_averaged_image(), autoLevels=False)

    def handle_roi_moved(self) -> None:
        """
        Handle changes to any ROI position and size.
        """
        roi_names = self.model.get_list_of_roi_names()
        for name in roi_names:
            roi = self.view.spectrum.get_roi(name)
            self.model.set_roi(name, roi)
            self.view.set_spectrum(self.model.get_spectrum(name, self.spectrum_mode))

    def handle_export_button_enabled(self) -> None:
        """
        Enable the export button if the current stack is not None
        """
        self.view.set_export_button_enabled(self.model.can_export())

    def handle_export_csv(self) -> None:
        path = self.view.get_csv_filename()
        if path is None:
            return

        if path.suffix != ".csv":
            path = path.with_suffix(".csv")

        self.model.save_csv(path, self.spectrum_mode == SpecType.SAMPLE_NORMED)

    def handle_enable_normalised(self, enabled: bool) -> None:
        if enabled:
            self.spectrum_mode = SpecType.SAMPLE_NORMED
        else:
            self.spectrum_mode = SpecType.SAMPLE
        self.handle_roi_moved()
        self.view.display_normalise_error()

    def get_roi_names(self) -> list:
        """
        Return a list of ROI names

        @return: list of ROI names
        """
        return self.model.get_list_of_roi_names()

    def do_add_roi(self) -> None:
        """
        Add a new ROI to the spectrum
        """
        roi_name = self.model.roi_name_generator()
        self.model.set_new_roi(roi_name)
        self.view.set_spectrum(self.model.get_spectrum(roi_name, self.spectrum_mode))
        self.view.spectrum.add_roi(self.model.get_roi(roi_name), roi_name)
        self.view.auto_range_image()
        self.do_add_roi_to_table(roi_name)

    def do_add_roi_to_table(self, roi_name: str) -> None:
        """
        Add a given ROI to the table by ROI name

        @param roi_name: Name of the ROI to add
        """
        row = self.model.selected_row
        roi_colour = self.view.spectrum.roi_dict[roi_name].colour
        self.view.add_roi_table_row(row, roi_name, roi_colour)

    def do_remove_roi(self, roi_name=None) -> None:
        """
        Remove a given ROI from the table by ROI name or all ROIs from the table

        @param roi_name: Name of the ROI to remove
        """

        if roi_name is None:
            self.model.remove_all_roi()

            for roi_item in self.get_roi_names():
                self.view.spectrum.remove_roi(roi_item)
        else:
            self.model.remove_roi(roi_name)
            self.view.spectrum.remove_roi(roi_name)

    def rename_roi(self, old_name: str, new_name: str) -> None:
        """
        Rename a given ROI from the table by ROI name

        @param old_name: Name of the ROI to rename
        @param new_name: New name of the ROI
        """
        self.model.rename_roi(old_name, new_name)
        self.view.spectrum.rename_roi(old_name, new_name)
