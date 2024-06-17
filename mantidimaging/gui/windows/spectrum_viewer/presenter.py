# Copyright (C) 2024 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

from enum import Enum
from functools import partial
from typing import TYPE_CHECKING

from logging import getLogger

import numpy as np
from PyQt5.QtCore import QSignalBlocker

from mantidimaging.core.data.dataset import StrictDataset
from mantidimaging.core.utility.sensible_roi import SensibleROI
from mantidimaging.gui.dialogs.async_task import start_async_task_view, TaskWorkerThread
from mantidimaging.gui.mvp_base import BasePresenter
from mantidimaging.gui.windows.spectrum_viewer.model import SpectrumViewerWindowModel, SpecType, ROI_RITS, ErrorMode, \
    ToFUnitMode, allowed_modes

if TYPE_CHECKING:
    from mantidimaging.gui.windows.spectrum_viewer.view import SpectrumViewerWindowView  # pragma: no cover
    from mantidimaging.gui.windows.main.view import MainWindowView  # pragma: no cover
    from mantidimaging.gui.windows.spectrum_viewer.spectrum_widget import SpectrumROI
    from mantidimaging.core.data import ImageStack
    from uuid import UUID
    from PyQt5.QtWidgets import QAction, QSpinBox

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
    view: SpectrumViewerWindowView
    model: SpectrumViewerWindowModel
    spectrum_mode: SpecType = SpecType.SAMPLE
    current_stack_uuid: UUID | None = None
    current_norm_stack_uuid: UUID | None = None
    export_mode: ExportMode

    def __init__(self, view: SpectrumViewerWindowView, main_window: MainWindowView):
        super().__init__(view)

        self.view = view
        self.main_window = main_window
        self.model = SpectrumViewerWindowModel(self)
        self.export_mode = ExportMode.ROI_MODE
        self.main_window.stack_changed.connect(self.handle_stack_changed)

    def handle_stack_changed(self) -> None:
        if self.current_stack_uuid:
            self.model.set_stack(self.main_window.get_stack(self.current_stack_uuid))
        else:
            return
        normalise_uuid = self.view.get_normalise_stack()
        if normalise_uuid is not None:
            try:
                norm_stack: ImageStack | None = self.main_window.get_stack(normalise_uuid)
            except RuntimeError:
                norm_stack = None
            self.model.set_normalise_stack(norm_stack)

        self.model.set_tof_unit_mode_for_stack()
        self.reset_units_menu()

        self.handle_tof_unit_change()
        self.show_new_sample()
        self.redraw_all_rois()

    def handle_sample_change(self, uuid: UUID | None) -> None:
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
            self.view.tof_mode_select_group.setEnabled(False)
            return

        self.model.set_stack(self.main_window.get_stack(uuid))
        self.model.set_tof_unit_mode_for_stack()
        self.reset_units_menu()

        self.handle_tof_unit_change()
        normalise_uuid = self.view.get_normalise_stack()
        if normalise_uuid is not None:
            try:
                norm_stack: ImageStack | None = self.main_window.get_stack(normalise_uuid)
            except RuntimeError:
                norm_stack = None
            self.model.set_normalise_stack(norm_stack)

        self.do_add_roi()
        self.add_rits_roi()
        self.view.set_normalise_error(self.model.normalise_issue())
        self.show_new_sample()
        self.view.on_visibility_change()

    def reset_units_menu(self):
        if self.model.tof_data is None:
            self.view.tof_mode_select_group.setEnabled(False)
            self.view.tofPropertiesGroupBox.setEnabled(False)
            self.model.tof_mode = ToFUnitMode.IMAGE_NUMBER
            self.change_selected_menu_option("Image Index")
            self.view.tof_mode_select_group.setEnabled(False)
        else:
            self.view.tof_mode_select_group.setEnabled(True)
            self.view.tofPropertiesGroupBox.setEnabled(True)

    def handle_normalise_stack_change(self, normalise_uuid: UUID | None) -> None:
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

    def get_dataset_id_for_stack(self, stack_id: UUID | None) -> UUID | None:
        return None if stack_id is None else self.main_window.get_dataset_id_from_stack_uuid(stack_id)

    def show_new_sample(self) -> None:
        """
        Show the new sample in the view and update the spectrum and
        image view accordingly. Resets the ROIs.
        """

        averaged_image = self.model.get_averaged_image()
        assert averaged_image is not None
        self.view.set_image(averaged_image)
        self.view.spectrum_widget.spectrum_plot_widget.add_range(*self.model.tof_plot_range)
        self.view.spectrum_widget.spectrum_plot_widget.set_image_index_range_label(*self.model.tof_range)
        self.view.auto_range_image()
        if self.view.get_roi_properties_spinboxes():
            self.view.set_roi_properties()

    def handle_range_slide_moved(self, tof_range) -> None:
        self.model.tof_plot_range = tof_range
        if self.model.tof_mode == ToFUnitMode.IMAGE_NUMBER:
            self.model.tof_range = (int(tof_range[0]), int(tof_range[1]))
        else:
            image_index_min = np.abs(self.model.tof_data - tof_range[0]).argmin()
            image_index_max = np.abs(self.model.tof_data - tof_range[1]).argmin()
            self.model.tof_range = tuple(sorted((image_index_min, image_index_max)))
        self.view.spectrum_widget.spectrum_plot_widget.set_image_index_range_label(*self.model.tof_range)
        self.view.spectrum_widget.spectrum_plot_widget.set_tof_range_label(*self.model.tof_plot_range)
        averaged_image = self.model.get_averaged_image()
        assert averaged_image is not None
        self.view.set_image(averaged_image, autoLevels=False)

    def handle_roi_moved(self, force_new_spectrums: bool = False) -> None:
        """
        Handle changes to any ROI position and size.
        """
        for name in self.model.get_list_of_roi_names():
            roi = self.view.spectrum_widget.get_roi(name)
            if force_new_spectrums or roi != self.model.get_roi(name):
                self.model.set_roi(name, roi)
                self.view.set_spectrum(name, self.model.get_spectrum(name, self.spectrum_mode))

    def handle_roi_clicked(self, roi: SpectrumROI) -> None:
        if not roi.name == ROI_RITS:
            self.view.current_roi_name = roi.name
            self.view.last_clicked_roi = roi.name
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
        self.view.update_roi_color(roi_name, new_colour)
        self.view.on_visibility_change()

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

    def handle_tof_unit_change(self) -> None:
        self.model.set_relevant_tof_units()
        tof_axis_label = allowed_modes[self.view.tof_units_mode]["label"]
        self.view.spectrum_widget.spectrum_plot_widget.set_tof_axis_label(tof_axis_label)
        self.refresh_spectrum_plot()

    def handle_tof_unit_change_via_menu(self) -> None:
        self.model.tof_mode = allowed_modes[self.view.tof_units_mode]["mode"]
        self.handle_tof_unit_change()

    def refresh_spectrum_plot(self) -> None:
        self.view.spectrum_widget.spectrum.clearPlots()
        self.view.spectrum_widget.spectrum.update()
        self.view.show_visible_spectrums()
        self.view.spectrum_widget.spectrum_plot_widget.add_range(*self.model.tof_plot_range)
        self.view.spectrum_widget.spectrum_plot_widget.set_image_index_range_label(*self.model.tof_range)
        self.view.auto_range_image()

    def handle_flight_path_change(self) -> None:
        self.model.units.target_to_camera_dist = self.view.flightPathSpinBox.value()
        self.model.set_relevant_tof_units()
        self.refresh_spectrum_plot()

    def handle_time_delay_change(self) -> None:
        self.model.units.data_offset = self.view.timeDelaySpinBox.value() * 1e-6
        self.model.set_relevant_tof_units()
        self.refresh_spectrum_plot()

    def change_selected_menu_option(self, opt):
        for action in self.view.tof_mode_select_group.actions():
            with QSignalBlocker(action):
                if action.objectName() == opt:
                    self.check_action(action, True)
                else:
                    self.check_action(action, False)

    def do_adjust_roi(self) -> None:
        new_roi = self.convert_spinbox_roi_to_SpectrumROI(self.view.roiPropertiesSpinBoxes)
        self.model.set_roi(self.view.current_roi_name, new_roi)
        self.view.spectrum_widget.adjust_roi(new_roi, self.view.current_roi_name)

    def handle_storing_current_roi_name_on_tab_change(self) -> None:
        old_table_names = self.view.old_table_names
        old_current_roi_name = self.view.current_roi_name
        old_last_clicked_roi = self.view.last_clicked_roi
        if self.export_mode == ExportMode.ROI_MODE:
            if old_current_roi_name == ROI_RITS and old_last_clicked_roi in old_table_names:
                self.view.current_roi_name = old_last_clicked_roi
            else:
                self.view.last_clicked_roi = old_current_roi_name
        elif self.export_mode == ExportMode.IMAGE_MODE:
            if (old_current_roi_name != ROI_RITS and old_current_roi_name in old_table_names
                    and old_last_clicked_roi != old_current_roi_name):
                self.view.last_clicked_roi = old_current_roi_name

    @staticmethod
    def check_action(action: QAction, param: bool) -> None:
        action.setChecked(param)

    def convert_spinbox_roi_to_SpectrumROI(self, spinboxes: dict[str, QSpinBox]) -> SpectrumROI:
        roi_iter_order = ["Left", "Top", "Right", "Bottom"]
        new_points = [spinboxes[prop].value() for prop in roi_iter_order]
        return SensibleROI().from_list(new_points)
