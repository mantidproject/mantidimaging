# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

import csv
from enum import Enum
from functools import partial
from typing import TYPE_CHECKING

from logging import getLogger

import numpy as np
from PyQt5.QtCore import QSignalBlocker, QTimer, Qt

from mantidimaging.core.fitting.fitting_functions import BadFittingRoiError
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

LOG = getLogger(__name__)


class ExportMode(Enum):
    # Needs to match GUI tab order
    ROI_MODE = 0
    IMAGE_MODE = 1


MODE_TO_LABEL = {v["mode"]: (k, v["label"]) for k, v in allowed_modes.items()}


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
    changed_roi: SpectrumROI
    image_nan_mask_dict: dict[str, np.ma.MaskedArray] = {}
    roi_to_process_queue: dict[str, SpectrumROI] = {}

    def __init__(self, view: SpectrumViewerWindowView, main_window: MainWindowView):
        super().__init__(view)

        self.view = view
        self.main_window = main_window
        self.model = SpectrumViewerWindowModel(self)
        self.export_mode = ExportMode.ROI_MODE
        self.main_window.stack_modified.connect(self.handle_stack_modified)

        self.handle_roi_change_timer = QTimer()
        self.handle_roi_change_timer.setSingleShot(True)
        self.handle_roi_change_timer.timeout.connect(self.handle_roi_moved)

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
        self.model.spectrum_cache.clear()
        sample_roi = SensibleROI.from_list([0, 0, *self.model.get_image_shape()])
        open_beam_roi = self.view.get_open_beam_roi()
        self.model.get_spectrum(sample_roi,
                                self.spectrum_mode,
                                self.view.shuttercount_norm_enabled(),
                                open_beam_roi=open_beam_roi)
        self.reset_units_menu()

        self.handle_tof_unit_change()
        self.show_new_sample()
        self.redraw_all_rois()

    def initial_roi_calc(self) -> None:
        sample_roi = SensibleROI.from_list([0, 0, *self.model.get_image_shape()])
        open_beam_roi = self.view.get_open_beam_roi()
        spectrum = self.model.get_spectrum(sample_roi,
                                           self.spectrum_mode,
                                           self.view.shuttercount_norm_enabled(),
                                           open_beam_roi=open_beam_roi)

        self.view.set_spectrum("roi", spectrum)

    def handle_sample_change(self, uuid: UUID | None) -> None:
        """
        Called when the stack has been changed in the stack selector.
        """
        self.view.roi_form.exportTabs.setDisabled(uuid is None)
        if self.current_stack_uuid and uuid:
            if ((current_stack := self.main_window.get_stack(self.current_stack_uuid))
                    and (new_stack := self.main_window.get_stack(uuid))):
                if current_stack.shape[1:] != new_stack.shape[1:]:
                    self.do_remove_roi()
                    self.view.table_view.clear_table()
                    LOG.info("The new image stack has a different size to previous image stack: deleting all ROIs")

        if uuid == self.current_stack_uuid:
            return
        else:
            self.current_stack_uuid = uuid
        new_dataset_id = self.get_dataset_id_for_stack(uuid)

        if new_dataset_id:
            self.auto_find_flat_stack(new_dataset_id)
        else:
            self.view.current_dataset_id = None

        self.model.spectrum_cache.clear()

        if uuid is None:
            self.model.set_stack(None)
            self._clear_state()
            self.view.tof_mode_select_group.setEnabled(False)
            return

        self.model.set_stack(self.main_window.get_stack(uuid))
        self.model.set_tof_unit_mode_for_stack()
        self.reset_units_menu()
        if not [name for name in self.view.spectrum_widget.roi_dict if name != 'rits_roi']:
            self.do_add_roi()
            self.add_rits_roi()
        self.roi_to_process_queue = self.view.spectrum_widget.roi_dict.copy()
        for roi in self.roi_to_process_queue.values():
            self.handle_notify_roi_moved(roi)
        self.handle_tof_unit_change()
        normalise_uuid = self.view.get_normalise_stack()
        if normalise_uuid is not None:
            try:
                norm_stack: ImageStack | None = self.main_window.get_stack(normalise_uuid)
            except RuntimeError:
                norm_stack = None
            self.model.set_normalise_stack(norm_stack)
        self.view.set_normalise_error(self.model.normalise_issue())
        self.set_shuttercount_error()
        self.show_new_sample()
        self.view.on_visibility_change()
        self.view.setup_roi_properties_spinboxes()

    def _clear_state(self) -> None:
        """Clear UI and data states when sample is removed. """
        self.model.set_normalise_stack(None)
        self.model.set_stack(None)
        self.current_norm_stack_uuid = None
        self.do_remove_roi()
        self.view.fittingForm.clear()
        self.view.fittingDisplayWidget.clear()
        self.view.clear()

    def reset_units_menu(self) -> None:
        if self.model.tof_data.size == 0:
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
        self.view.fittingDisplayWidget.update_image(averaged_image)

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
            image_index_min = np.abs(self.model.tof_data - tof_range[0]).argmin()
            image_index_max = np.abs(self.model.tof_data - tof_range[1]).argmin()
            self.model.tof_range = tuple(sorted((image_index_min, image_index_max)))
        self.view.spectrum_widget.spectrum_plot_widget.set_image_index_range_label(*self.model.tof_range)
        self.view.spectrum_widget.spectrum_plot_widget.set_tof_range_label(*self.model.tof_plot_range)
        self.update_displayed_image(autoLevels=False)
        LOG.info("Projection range changed: ToF Range = %s", self.model.tof_range)

    def handle_notify_roi_moved(self, roi: SpectrumROI) -> None:
        self.changed_roi = roi
        self.view.roi_form.roi_properties_widget.update_roi_limits(roi.as_sensible_roi())
        run_thread_check = roi not in self.roi_to_process_queue
        self.roi_to_process_queue[self.changed_roi.name] = self.changed_roi
        spectrum = self.view.spectrum_widget.spectrum_data_dict[roi.name]
        if spectrum is not None:
            self.image_nan_mask_dict[roi.name] = np.ma.asarray(np.full(self.model.get_stack_length(), np.nan))
        self.clear_spectrum()
        self.view.show_visible_spectrums()
        self.view.spectrum_widget.spectrum.update()
        if run_thread_check:
            if not self.handle_roi_change_timer.isActive():
                self.handle_roi_change_timer.start(500)

    def run_spectrum_calculation(self, roi: SpectrumROI, open_beam_roi: SensibleROI | None, spec_mode: SpecType,
                                 shutter_norm: bool, chunk_start: int, chunk_end: int) -> np.ndarray:
        spectrum = self.model.get_spectrum(roi.as_sensible_roi(),
                                           spec_mode,
                                           shutter_norm,
                                           chunk_start,
                                           chunk_end,
                                           open_beam_roi=open_beam_roi)
        return spectrum

    def spectrum_calculation_setup(self) -> tuple[int, int]:
        queue = self.roi_to_process_queue
        mask = self.image_nan_mask_dict
        roi_name = list(queue.keys())[0]
        chunk_size = 100
        if chunk_size > 0:
            nanInds = np.argwhere(np.isnan(mask[roi_name]))
            chunk_start = int(nanInds[0, 0])
            if len(nanInds) > chunk_size:
                chunk_end = int(nanInds[chunk_size, 0])
            else:
                chunk_end = int(nanInds[-1, 0]) + 1
        else:
            chunk_start, chunk_end = (0, -1)

        return chunk_start, chunk_end

    def handle_roi_moved(self) -> None:
        """
        Handle changes to any ROI position and size.
        """
        chunk_start, chunk_end = self.spectrum_calculation_setup()
        self.thread = TaskWorkerThread()
        self.thread.task_function = self.run_spectrum_calculation
        self.thread.kwargs = {
            "roi": list(self.roi_to_process_queue.values())[0],
            "open_beam_roi": self.view.get_open_beam_roi(),
            "spec_mode": self.spectrum_mode,
            "shutter_norm": self.view.shuttercount_norm_enabled(),
            "chunk_start": chunk_start,
            "chunk_end": chunk_end,
        }
        self.thread.finished.connect(lambda: self.thread_cleanup(self.thread))
        self.thread.start()

    def thread_cleanup(self, thread: TaskWorkerThread) -> None:
        if thread.error is not None:
            raise thread.error
        if self.thread.result is not None:
            self.thread_finished_processing(self.thread)
        self.view.show_visible_spectrums()
        self.view.spectrum_widget.spectrum.update()
        if np.isnan(self.image_nan_mask_dict[list(self.roi_to_process_queue.keys())[0]]).any():
            self.try_next_mean_chunk()
        else:
            self.roi_to_process_queue.pop(list(self.roi_to_process_queue.keys())[0])
        if len(self.roi_to_process_queue) > 0:
            self.try_next_mean_chunk()
        else:
            self.view.show_visible_spectrums()
            self.view.spectrum_widget.spectrum.update()

        roi = self.changed_roi.as_sensible_roi()
        coords = (roi.left, roi.top, roi.right, roi.bottom)
        if coords != getattr(self, "_last_logged_roi_coords", None):
            LOG.info("ROI moved: name=%s, new coords=Left: %d, Top: %d, Right: %d, Bottom: %d", self.changed_roi.name,
                     *coords)
            self._last_logged_roi_coords = coords

    def thread_finished_processing(self, thread: TaskWorkerThread) -> None:
        if thread.result is not None:
            spectrum = thread.result
            roi_name = thread.kwargs["roi"].name
            chunk_start = thread.kwargs["chunk_start"]
            spectrum_data_dict = self.view.spectrum_widget.spectrum_data_dict[roi_name]

            if spectrum_data_dict is not None:
                for i in range(len(spectrum)):
                    np.put(spectrum_data_dict, chunk_start + i, spectrum[i])
                    if np.isnan(spectrum[i]):
                        self.image_nan_mask_dict[roi_name][chunk_start + i] = np.ma.masked
                    else:
                        np.put(self.image_nan_mask_dict[roi_name], chunk_start + i, spectrum[i])

    def try_next_mean_chunk(self) -> None:
        if list(self.roi_to_process_queue.keys())[0] not in self.view.spectrum_widget.spectrum_data_dict.keys():
            return
        spectrum = self.image_nan_mask_dict[list(self.roi_to_process_queue.keys())[0]]
        if spectrum is not None:
            if np.isnan(spectrum).any():
                if not self.handle_roi_change_timer.isActive():
                    self.handle_roi_change_timer.start(10)
            else:
                self.model.store_spectrum(self.changed_roi.as_sensible_roi(), self.spectrum_mode,
                                          self.view.shuttercount_norm_enabled(), spectrum)

    def handle_roi_clicked(self, roi: SpectrumROI) -> None:
        if not roi.name == ROI_RITS:
            self.view.table_view.select_roi(roi.name)
            self.view.set_roi_properties()

    def clear_spectrum(self) -> None:
        self.view.spectrum_widget.spectrum_data_dict[self.changed_roi.name] = (np.full(
            self.model.get_number_of_images_in_stack(), np.nan))

    @property
    def fitting_spectrum(self) -> np.ndarray:
        return self.view.fittingForm.presenter.fitting_spectrum[1]

    def redraw_spectrum(self, name: str) -> None:
        """
        Redraw the spectrum with the given name
        """
        sample_roi = self.view.spectrum_widget.get_roi(name)
        open_beam_roi = self._resolve_open_beam_roi()

        spectrum = self.model.get_spectrum(
            sample_roi,
            self.spectrum_mode,
            self.view.shuttercount_norm_enabled(),
            open_beam_roi=open_beam_roi,
        )

        self.view.set_spectrum(name, spectrum)

    def _resolve_open_beam_roi(self) -> SensibleROI | None:
        """
        Return the chosen open-beam ROI from the dropdown, or None to use the same ROI.
        """
        choice = self.view.get_open_beam_roi_choice()
        if choice == "Use same ROI":
            return None
        return self.view.spectrum_widget.get_roi(choice)

    def handle_open_beam_roi_choice_changed(self) -> None:
        self.redraw_all_rois()

    def redraw_all_rois(self) -> None:
        """
        Redraw all ROIs and spectrum plots
        """
        for roi_name, roi_widget in self.view.spectrum_widget.roi_dict.items():
            if roi_widget.isVisible():
                self.redraw_spectrum(roi_name)

    def handle_roi_name_change(self, old_name: str, new_name: str) -> None:
        self.view.spectrum_widget.rename_roi(old_name, new_name)
        self.view.set_roi_properties()

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
        LOG.info("CSV export successful: file saved to '%s'", path)

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
                self.view.get_binner(),
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
            LOG.error("Fit failed: %s", task.error)

    def handle_enable_normalised(self, enabled: bool) -> None:
        if not self.model.has_stack():
            return
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
        LOG.info(f"ROI created: name={roi_name}, coords=({roi.left}, {roi.right}, {roi.top}, {roi.bottom})")
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
        open_beam_roi = self._resolve_open_beam_roi()
        self.view.spectrum_widget.add_roi(roi, ROI_RITS)
        spectrum = self.model.get_spectrum(
            roi,
            self.spectrum_mode,
            self.view.shuttercount_norm_enabled(),
            open_beam_roi=open_beam_roi,
        )
        self.view.set_spectrum(ROI_RITS, spectrum)
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
                LOG.info(f"ROI removed: name={name}")
            self.view.spectrum_widget.roi_dict.clear()
            self.view.table_view.clear_table()
            self.model.remove_all_roi()
        else:
            self.view.spectrum_widget.remove_roi(roi_name)
            LOG.info(f"ROI removed: name={roi_name}")
        self.view.update_roi_dropdown()

    def handle_export_tab_change(self, index: int) -> None:
        self.export_mode = ExportMode(index)
        self.view.on_visibility_change()

    def handle_tof_unit_change(self) -> None:
        self.model.set_relevant_tof_units()
        self.update_unit_labels_and_menus()
        self.refresh_spectrum_plot()

    def handle_tof_unit_change_via_menu(self, unit_name: str) -> None:
        self.view.tof_units_mode = unit_name
        self.model.tof_mode = allowed_modes[unit_name]["mode"]
        self.handle_tof_unit_change()

    def update_unit_labels_and_menus(self) -> None:
        """
        Update all unit-related axis and range labels, as well as unit selection menus
        in both the main spectrum plot in the image tab and the fitting tab.
        """
        unit_mode = self.model.tof_mode
        tof_data = self.model.tof_data

        unit_name, axis_label = MODE_TO_LABEL.get(unit_mode, ("Image Index", allowed_modes["Image Index"]["label"]))

        # Update axis labels
        self.view.spectrum_widget.spectrum_plot_widget.set_tof_axis_label(axis_label)
        self.view.fittingDisplayWidget.spectrum_plot.spectrum.setLabel('bottom', text=axis_label)

        # Update range labels
        if tof_data.size > 0:
            range_min, range_max = float(np.min(tof_data)), float(np.max(tof_data))
            self.view.spectrum_widget.spectrum_plot_widget.set_tof_range_label(range_min, range_max)
            self.view.fittingDisplayWidget.spectrum_plot.set_tof_range_label(range_min, range_max)
            self.view.fittingDisplayWidget.spectrum_plot.set_unit_range_label(range_min, range_max, axis_label)

        self.view.sync_unit_menus(unit_name)

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
                action.setChecked(action.objectName() == opt)

    def do_adjust_roi(self) -> None:
        new_roi = self.view.roi_form.roi_properties_widget.to_roi()
        if self.export_mode == ExportMode.ROI_MODE:
            roi_name = self.view.table_view.current_roi_name
        elif self.export_mode == ExportMode.IMAGE_MODE:
            roi_name = "rits_roi"
        self.view.spectrum_widget.adjust_roi(new_roi, roi_name)
        self.handle_notify_roi_moved(self.view.spectrum_widget.roi_dict[roi_name])

    def fit_all_regions(self) -> None:
        init_params = self.view.fitting_param_form.get_initial_param_values()
        bound_params = self.view.fitting_param_form.get_bound_parameters()
        for roi_name, roi_widget in self.view.spectrum_widget.roi_dict.items():
            if roi_name == "rits_roi":
                continue
            roi = roi_widget.as_sensible_roi()
            spectrum = self.model.get_spectrum(roi, self.spectrum_mode, self.view.shuttercount_norm_enabled())
            fitting_region = self.view.get_fitting_region()
            try:
                result, rss, rss_per_dof = self.model.fit_single_region(spectrum,
                                                                        fitting_region,
                                                                        self.model.tof_data,
                                                                        init_params,
                                                                        bounds=bound_params)
                status = "Fitted"
            except (ValueError, BadFittingRoiError) as e:
                LOG.warning(f"Failed to find fit for ROI '{roi_name}': {e}")
                param_names = self.model.fitting_engine.get_parameter_names()
                result = {param_name: 0 for param_name in param_names}
                status = "Failed"
                rss_per_dof = 0

            self.view.exportDataTableWidget.update_roi_data(
                roi_name=roi_name,
                params=result,
                status=status,
                chi2=rss_per_dof,
            )
            LOG.info("Fit completed for ROI=%s, params=%s, RSS/DoF=%.3f", roi_name, result, rss_per_dof)

    def handle_export_table(self) -> None:
        """
        Export the ROI fitting results table to CSV.
        """
        path = self.view.get_csv_filename()
        if not path:
            LOG.warning("Export cancelled: no file path selected.")
            return

        path = path.with_suffix(".csv") if path.suffix != ".csv" else path
        selected_roi = self.view.exportSettingsWidget.selected_area()
        export_format = self.view.exportSettingsWidget.selected_format()
        model = self.view.exportDataTableWidget.model

        LOG.info("User initiated export: format=%s, area=%s, path=%s", export_format, selected_roi, path)

        with open(path, 'w', newline='') as file:
            writer = csv.writer(file)
            headers = [model.headerData(i, Qt.Horizontal) for i in range(model.columnCount())]
            writer.writerow(headers)
            for row in range(model.rowCount()):
                roi_name = model.item(row, 0).text()
                if selected_roi != "All" and roi_name != selected_roi:
                    continue
                row_data = [model.item(row, col).data() for col in range(model.columnCount())]
                writer.writerow(row_data)
