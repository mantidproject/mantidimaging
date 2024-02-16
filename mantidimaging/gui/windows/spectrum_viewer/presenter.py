# Copyright (C) 2023 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

from enum import Enum
from functools import partial
from typing import TYPE_CHECKING, Optional

from logging import getLogger
from mantidimaging.core.data.dataset import StrictDataset
from mantidimaging.gui.dialogs.async_task import start_async_task_view, TaskWorkerThread
from mantidimaging.gui.mvp_base import BasePresenter
from mantidimaging.gui.windows.spectrum_viewer.model import SpectrumViewerWindowModel, SpecType, ROI_RITS, ErrorMode

if TYPE_CHECKING:
    from mantidimaging.gui.windows.spectrum_viewer.view import SpectrumViewerWindowView  # pragma: no cover
    from mantidimaging.gui.windows.main.view import MainWindowView  # pragma: no cover
    from mantidimaging.core.data import ImageStack
    from uuid import UUID

LOG = getLogger(__name__)


class ExportMode(Enum):
    # Needs to match GUI tab order
    ROI_MODE = 0
    IMAGE_MODE = 1


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
    export_mode: ExportMode

    def __init__(self, view: 'SpectrumViewerWindowView', main_window: 'MainWindowView'):
        super().__init__(view)

        self.view = view
        self.main_window = main_window
        self.model = SpectrumViewerWindowModel(self)
        self.export_mode = ExportMode.ROI_MODE

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

        self.do_remove_roi()
        if uuid is None:
            self.model.set_stack(None)
            self.view.clear()
            return

        self.model.set_stack(self.main_window.get_stack(uuid))
        normalise_uuid = self.view.get_normalise_stack()
        if normalise_uuid is not None:
            try:
                norm_stack: Optional['ImageStack'] = self.main_window.get_stack(normalise_uuid)
            except RuntimeError:
                norm_stack = None
            self.model.set_normalise_stack(norm_stack)

        self.do_add_roi()
        self.add_rits_roi()
        self.view.set_normalise_error(self.model.normalise_issue())
        self.show_new_sample()

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
        if self.view.normalisation_enabled():
            self.redraw_all_rois()

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
        """
        Show the new sample in the view and update the spectrum and
        image view accordingly. Resets the ROIs.
        """

        self.view.set_image(self.model.get_averaged_image())
        self.view.spectrum_widget.spectrum_plot_widget.add_range(*self.model.tof_range)
        self.view.auto_range_image()
        if self.view.get_roi_properties_spinboxes():
            self.view.set_roi_properties()

    def handle_range_slide_moved(self, tof_range) -> None:
        self.model.tof_range = tof_range
        self.view.set_image(self.model.get_averaged_image(), autoLevels=False)

    def handle_roi_moved(self, force_new_spectrums: bool = False) -> None:
        """
        Handle changes to any ROI position and size.
        """
        for name in self.model.get_list_of_roi_names():
            roi = self.view.spectrum_widget.get_roi(name)
            if force_new_spectrums or roi != self.model.get_roi(name):
                self.model.set_roi(name, roi)
                self.view.set_spectrum(name, self.model.get_spectrum(name, self.spectrum_mode))

    def handle_roi_clicked(self, roi) -> None:
        self.view.current_roi = roi.name
        self.view.set_roi_properties()

    def redraw_spectrum(self, name: str) -> None:
        """
        Redraw the spectrum with the given name
        """
        self.view.set_spectrum(name, self.model.get_spectrum(name, self.spectrum_mode))

    def redraw_all_rois(self) -> None:
        """
        Redraw all ROIs and spectrum plots
        """
        for name in self.model.get_list_of_roi_names():
            self.model.set_roi(name, self.view.spectrum_widget.get_roi(name))
            self.view.set_spectrum(name, self.model.get_spectrum(name, self.spectrum_mode))

    def handle_button_enabled(self) -> None:
        """
        Enable the export button if the current stack is not None and normalisation is valid
        """
        has_stack = self.model.has_stack()
        normalisation_on = self.view.normalisation_enabled()
        normalisation_no_error = (normalisation_on and self.model.normalise_issue() == "") or not normalisation_on

        self.view.exportButton.setEnabled(has_stack and normalisation_no_error)
        self.view.exportButtonRITS.setEnabled(has_stack and normalisation_on and normalisation_no_error)
        self.view.addBtn.setEnabled(has_stack)

    def handle_export_csv(self) -> None:
        path = self.view.get_csv_filename()
        if path is None:
            return

        if path.suffix != ".csv":
            path = path.with_suffix(".csv")

        self.model.save_csv(path, self.spectrum_mode == SpecType.SAMPLE_NORMED)

    def handle_rits_export(self) -> None:
        """
        Handle the export of the current spectrum to a RITS file format
        """
        error_mode = ErrorMode.get_by_value(self.view.transmission_error_mode)

        if self.view.image_output_mode == "2D Binned":
            path = self.view.get_rits_export_directory()
            if path is None:
                LOG.debug("No path selected, aborting export")
                return
            run_function = partial(self.model.save_rits_images, path, error_mode, self.view.bin_size,
                                   self.view.bin_step)

            start_async_task_view(self.view, run_function, self._async_save_done)

        else:
            path = self.view.get_rits_export_filename()
            if path is None:
                LOG.debug("No path selected, aborting export")
                return
            if path and path.suffix != ".dat":
                path = path.with_suffix(".dat")
            self.model.save_single_rits_spectrum(path, error_mode)

    def _async_save_done(self, task: TaskWorkerThread) -> None:
        if task.error is not None:
            self.view.show_error_dialog(f"Operation failed: {task.error}")

    def handle_enable_normalised(self, enabled: bool) -> None:
        if enabled:
            self.spectrum_mode = SpecType.SAMPLE_NORMED
        else:
            self.spectrum_mode = SpecType.SAMPLE
        self.redraw_all_rois()
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
        self.view.spectrum_widget.add_roi(self.model.get_roi(roi_name), roi_name)
        self.view.set_spectrum(roi_name, self.model.get_spectrum(roi_name, self.spectrum_mode))
        self.view.auto_range_image()
        self.do_add_roi_to_table(roi_name)

    def change_roi_colour(self, roi_name: str, new_colour: tuple) -> None:
        """
        Change the colour of a given ROI in both the spectrum widget and the table.

        @param roi_name: Name of the ROI to change color.
        @param new_colour: The new color for the ROI.
        """
        if roi_name in self.view.spectrum_widget.roi_dict:
            self.view.spectrum_widget.roi_dict[roi_name].colour = new_colour
        self.view.update_roi_color_in_table(roi_name, new_colour)

    def add_rits_roi(self) -> None:
        roi_name = ROI_RITS
        self.model.set_new_roi(roi_name)
        self.view.spectrum_widget.add_roi(self.model.get_roi(roi_name), roi_name)
        self.view.set_spectrum(roi_name, self.model.get_spectrum(roi_name, self.spectrum_mode))
        self.view.set_roi_alpha(0, ROI_RITS)

    def do_add_roi_to_table(self, roi_name: str) -> None:
        """
        Add a given ROI to the table by ROI name

        @param roi_name: Name of the ROI to add
        """
        roi_colour = self.view.spectrum_widget.roi_dict[roi_name].colour
        self.view.add_roi_table_row(roi_name, roi_colour)

    def rename_roi(self, old_name: str, new_name: str) -> None:
        """
        Rename a given ROI from the table by ROI name

        @param old_name: Name of the ROI to rename
        @param new_name: New name of the ROI
        """
        self.view.spectrum_widget.rename_roi(old_name, new_name)
        self.model.rename_roi(old_name, new_name)

    def do_remove_roi(self, roi_name: str | None = None) -> None:
        """
        Remove a given ROI from the table by ROI name or all ROIs from
        the table if no name is passed as an argument

        @param roi_name: Name of the ROI to remove
        """
        if roi_name is None:
            self.view.clear_all_rois()
            for roi in self.get_roi_names():
                self.view.spectrum_widget.remove_roi(roi)
            self.model.remove_all_roi()
        else:
            self.view.spectrum_widget.remove_roi(roi_name)
            self.view.set_spectrum(roi_name, self.model.get_spectrum(roi_name, self.spectrum_mode))
            self.model.remove_roi(roi_name)

    def handle_export_tab_change(self, index: int) -> None:
        self.export_mode = ExportMode(index)
        self.view.on_visibility_change()
