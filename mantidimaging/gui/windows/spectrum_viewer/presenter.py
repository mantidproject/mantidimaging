# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

from enum import Enum
from functools import partial
from typing import TYPE_CHECKING

from logging import getLogger

import numpy as np
from PyQt5.QtCore import QSignalBlocker

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
    from PyQt5.QtWidgets import QAction

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
        self.main_window.stack_changed.connect(self.handle_stack_modified)

    def handle_stack_modified(self) -> None:
        """
        Called when an image stack is modified somewhere else in MI, for example in the operations window
        """
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
        """
        Called when the stack has been changed in the stack selector.
        """
        self.view.roi_form.exportTabs.setDisabled(uuid is None)

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
        self.set_shuttercount_error()
        self.show_new_sample()
        self.view.on_visibility_change()
        self.view.setup_roi_properties_spinboxes()

    def reset_units_menu(self) -> None:
        if self.model.tof_data is None:
            self.view.tof_mode_select_group.setEnabled(False)
            self.view.experimentSetupGroupBox.setEnabled(False)
            self.model.tof_mode = ToFUnitMode.IMAGE_NUMBER
            self.change_selected_menu_option("Image Index")
            self.view.tof_mode_select_group.setEnabled(False)
        else:
            self.view.tof_mode_select_group.setEnabled(True)
            self.view.experimentSetupGroupBox.setEnabled(True)

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
        self.set_shuttercount_error()
        if self.view.normalisation_enabled():
            self.redraw_all_rois()
            self.update_displayed_image(autoLevels=True)

    def auto_find_flat_stack(self, new_dataset_id: UUID) -> None:
        if self.view.current_dataset_id != new_dataset_id:
            self.view.current_dataset_id = new_dataset_id

            new_dataset = self.main_window.get_dataset(new_dataset_id)
            if new_dataset is not None:
                if new_dataset.flat_before is not None:
                    self.view.try_to_select_relevant_normalise_stack(new_dataset.flat_before.name)
                elif new_dataset.flat_after is not None:
                    self.view.try_to_select_relevant_normalise_stack(new_dataset.flat_after.name)

    def get_dataset_id_for_stack(self, stack_id: UUID | None) -> UUID | None:
        return None if stack_id is None else self.main_window.get_dataset_id_from_stack_uuid(stack_id)

    def update_displayed_image(self, autoLevels: bool = True) -> None:
        """Fetches the correct image (normalized or not) and updates the display."""
        averaged_image = (self.model.get_normalized_averaged_image()
                          if self.view.normalisation_enabled() else self.model.get_averaged_image())
        if averaged_image is None:
            image_shape = self.model.get_image_shape()
            averaged_image = np.zeros(image_shape, dtype=np.float32)
        self.view.set_image(averaged_image, autoLevels=autoLevels)

    def show_new_sample(self) -> None:
        """
        Show the new sample in the view and update the spectrum and
        image view accordingly. Resets the ROIs.
        """
        averaged_image = self.model.get_averaged_image()
        assert averaged_image is not None
        self.update_displayed_image(autoLevels=True)
        self.view.spectrum_widget.spectrum_plot_widget.add_range(*self.model.tof_plot_range)
        self.view.spectrum_widget.spectrum_plot_widget.set_image_index_range_label(*self.model.tof_range)
        self.view.auto_range_image()
        self.view.set_roi_properties()

    def handle_range_slide_moved(self, tof_range: tuple[float, float] | tuple[int, int]) -> None:
        self.model.tof_plot_range = tof_range
        if self.model.tof_mode == ToFUnitMode.IMAGE_NUMBER:
            self.model.tof_range = (int(tof_range[0]), int(tof_range[1]))
        else:
            assert self.model.tof_data is not None
            image_index_min = np.abs(self.model.tof_data - tof_range[0]).argmin()
            image_index_max = np.abs(self.model.tof_data - tof_range[1]).argmin()
            self.model.tof_range = tuple(sorted((image_index_min, image_index_max)))
        self.view.spectrum_widget.spectrum_plot_widget.set_image_index_range_label(*self.model.tof_range)
        self.view.spectrum_widget.spectrum_plot_widget.set_tof_range_label(*self.model.tof_plot_range)
        self.update_displayed_image(autoLevels=False)

    def handle_roi_moved(self, roi: SpectrumROI) -> None:
        """
        Handle changes to any ROI position and size.
        """
        spectrum = self.model.get_spectrum(
            roi.as_sensible_roi(),
            self.spectrum_mode,
            self.view.shuttercount_norm_enabled(),
        )
        self.view.set_spectrum(roi.name, spectrum)

    def handle_roi_clicked(self, roi: SpectrumROI) -> None:
        if not roi.name == ROI_RITS:
            self.view.table_view.select_roi(roi.name)
            self.view.set_roi_properties()

    def update_fitting_spectrum(self, roi_name: str, reset_region: bool = False) -> None:
        """
        Fetches the spectrum data for the selected ROI and updates the fitting display plot.
        """
        if roi_name not in self.view.spectrum_widget.roi_dict:
            return
        roi = self.view.spectrum_widget.get_roi(roi_name)
        spectrum_data = self.model.get_spectrum(roi, self.spectrum_mode)
        tof_data = self.model.tof_data
        if tof_data is None:
            return

        image = (self.model.get_normalized_averaged_image()
                 if self.view.normalisation_enabled() else self.model.get_averaged_image())

        self.view.fittingDisplayWidget.update_plot(tof_data, spectrum_data, label=roi_name, image=image)
        wavelength_range = float(np.min(tof_data)), float(np.max(tof_data))
        roi_widget = self.view.spectrum_widget.roi_dict[roi_name]
        self.view.fittingDisplayWidget.show_roi_on_thumbnail_from_widget(roi_widget)
        self.setup_fitting_model()
        self.view.fittingDisplayWidget.update_labels(wavelength_range=wavelength_range)
        if reset_region:
            self.view.fittingDisplayWidget.set_default_region(tof_data, spectrum_data)

    def redraw_spectrum(self, name: str) -> None:
        """
        Redraw the spectrum with the given name
        """
        roi = self.view.spectrum_widget.get_roi(name)
        spectrum = self.model.get_spectrum(roi, self.spectrum_mode, self.view.shuttercount_norm_enabled())
        self.view.set_spectrum(name, spectrum)

    def redraw_all_rois(self) -> None:
        """
        Redraw all ROIs and spectrum plots
        """
        for roi_name, roi_widget in self.view.spectrum_widget.roi_dict.items():
            if not roi_widget.isVisible():
                continue
            widget_roi = self.view.spectrum_widget.get_roi(roi_name)
            spectrum = self.model.get_spectrum(widget_roi, self.spectrum_mode, self.view.shuttercount_norm_enabled())
            self.view.set_spectrum(roi_name, spectrum)

    def handle_button_enabled(self) -> None:
        """
        Enable the export button if the current stack is not None and normalisation is valid
        """
        has_stack = self.model.has_stack()
        normalisation_on = self.view.normalisation_enabled()
        normalisation_no_error = (normalisation_on and self.model.normalise_issue() == "") or not normalisation_on

        self.view.roi_form.exportButton.setEnabled(has_stack and normalisation_no_error)
        self.view.roi_form.exportButtonRITS.setEnabled(has_stack and normalisation_on and normalisation_no_error)
        self.view.roi_form.addBtn.setEnabled(has_stack)
        self.view.normalise_ShutterCount_CheckBox.setEnabled(has_stack and normalisation_on and normalisation_no_error)
        if not self.view.normalise_ShutterCount_CheckBox.isEnabled():
            self.view.normalise_ShutterCount_CheckBox.setChecked(False)

    def handle_export_csv(self) -> None:
        path = self.view.get_csv_filename()
        if not path:
            return
        path = path.with_suffix(".csv") if path.suffix != ".csv" else path
        rois = {roi.name: roi.as_sensible_roi() for roi in self.view.spectrum_widget.roi_dict.values()}

        self.model.save_csv(
            path,
            rois,
            normalise=self.spectrum_mode == SpecType.SAMPLE_NORMED,
            normalise_with_shuttercount=self.view.shuttercount_norm_enabled(),
        )

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
            roi = self.view.spectrum_widget.get_roi(ROI_RITS)
            run_function = partial(
                self.model.save_rits_images,
                path,
                error_mode,
                self.view.bin_size,
                self.view.bin_step,
                roi,
                normalise=self.view.shuttercount_norm_enabled(),
            )
            start_async_task_view(self.view, run_function, self._async_save_done)
        else:
            path = self.view.get_rits_export_filename()
            if path is None:
                LOG.debug("No path selected, aborting export")
                return
            if path and path.suffix != ".dat":
                path = path.with_suffix(".dat")
            roi = self.view.spectrum_widget.get_roi(ROI_RITS)
            self.model.save_single_rits_spectrum(path, error_mode, roi)

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
        self.update_displayed_image(autoLevels=True)

    def set_shuttercount_error(self, enabled: bool = False) -> None:
        """
        Set ShutterCount error message when a valid normalisation stack has been selected and
        shuttercount correction has been toggled on and redraw all ROIs to ensure the spectrum
        is updated when ShutterCount correction is toggled between enabled and disabled states.
        """
        if self.spectrum_mode is SpecType.SAMPLE_NORMED:
            self.view.set_shuttercount_error(self.model.shuttercount_issue() if enabled else "")
            self.redraw_all_rois()

    def get_roi_names(self) -> list[str]:
        """
        @return: list of ROI names
        """
        return list(self.view.spectrum_widget.roi_dict.keys())

    def do_add_roi(self) -> None:
        """
        Add a new ROI to the spectrum
        """
        roi_name = self.model.roi_name_generator()
        if roi_name in self.view.spectrum_widget.roi_dict:
            raise ValueError(f"ROI name already exists: {roi_name}")
        height, width = self.model.get_image_shape()
        roi = SensibleROI.from_list([0, 0, width, height])
        self.view.spectrum_widget.add_roi(roi, roi_name)
        spectrum = self.model.get_spectrum(roi, self.spectrum_mode, self.view.shuttercount_norm_enabled())
        self.view.set_spectrum(roi_name, spectrum)
        self.view.auto_range_image()
        self.do_add_roi_to_table(roi_name)
        self.view.update_roi_dropdown()

    def change_roi_colour(self, roi_name: str, new_colour: tuple[int, int, int, int]) -> None:
        """
        Change the colour of a given ROI in both the spectrum widget and the table.

        @param roi_name: Name of the ROI to change color.
        @param new_colour: The new color for the ROI.
        """
        if roi_name in self.view.spectrum_widget.roi_dict:
            self.view.spectrum_widget.roi_dict[roi_name].colour = new_colour
        self.view.table_view.update_roi_color(roi_name, new_colour)
        self.view.on_visibility_change()

    def add_rits_roi(self) -> None:
        """
        Add the RITS ROI to the spectrum widget and initialize it with default dimensions.
        """
        roi = SensibleROI.from_list([0, 0, *self.model.get_image_shape()])
        self.view.spectrum_widget.add_roi(roi, ROI_RITS)
        self.view.set_spectrum(ROI_RITS,
                               self.model.get_spectrum(roi, self.spectrum_mode, self.view.shuttercount_norm_enabled()))
        self.view.set_roi_visibility_flags(ROI_RITS, visible=False)

    def do_add_roi_to_table(self, roi_name: str) -> None:
        """
        Add a given ROI to the table by ROI name

        @param roi_name: Name of the ROI to add
        """
        roi_colour = self.view.spectrum_widget.roi_dict[roi_name].colour
        self.view.add_roi_table_row(roi_name, roi_colour)

    def do_remove_roi(self, roi_name: str | None = None) -> None:
        """
        Remove a given ROI from the table by ROI name or all ROIs from
        the table if no name is passed as an argument

        @param roi_name: Name of the ROI to remove
        """
        if roi_name is None:
            for name in list(self.get_roi_names()):
                self.view.spectrum_widget.remove_roi(name)
            self.view.spectrum_widget.roi_dict.clear()
            self.view.table_view.clear_table()
            self.model.remove_all_roi()
        else:
            self.view.spectrum_widget.remove_roi(roi_name)
        self.view.update_roi_dropdown()

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
        self.view.show_visible_spectrums()
        self.view.spectrum_widget.spectrum_plot_widget.add_range(*self.model.tof_plot_range)
        self.view.spectrum_widget.spectrum_plot_widget.set_image_index_range_label(*self.model.tof_range)
        self.view.auto_range_image()

    def handle_experiment_setup_properties_change(self) -> None:
        self.model.units.target_to_camera_dist = self.view.experimentSetupFormWidget.flight_path
        self.model.units.data_offset = self.view.experimentSetupFormWidget.time_delay * 1e-6
        self.model.set_relevant_tof_units()
        self.refresh_spectrum_plot()

    def change_selected_menu_option(self, opt: str) -> None:
        for action in self.view.tof_mode_select_group.actions():
            with QSignalBlocker(action):
                if action.objectName() == opt:
                    self.check_action(action, True)
                else:
                    self.check_action(action, False)

    def do_adjust_roi(self) -> None:
        new_roi = self.view.roi_form.roi_properties_widget.to_roi()
        roi_name = self.view.table_view.current_roi_name
        self.view.spectrum_widget.adjust_roi(new_roi, roi_name)
        self.handle_roi_moved(self.view.spectrum_widget.roi_dict[roi_name])

    @staticmethod
    def check_action(action: QAction, param: bool) -> None:
        action.setChecked(param)

    def setup_fitting_model(self) -> None:
        parameter_names = self.model.fitting_engine.get_parameter_names()
        self.view.scalable_roi_widget.set_parameters(parameter_names)

    def get_init_params_from_roi(self):
        fitting_region = self.view.get_fitting_region()
        init_params = self.model.fitting_engine.get_init_params_from_roi(fitting_region)
        self.view.scalable_roi_widget.set_parameter_values(init_params)
