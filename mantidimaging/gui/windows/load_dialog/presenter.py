# Copyright (C) 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later

import os
import traceback
from enum import auto, Enum
from logging import getLogger
from pathlib import Path
from typing import TYPE_CHECKING, Optional

from mantidimaging.core.io.loader import load_log
from mantidimaging.core.io.loader.loader import read_in_file_information, FileInformation
from mantidimaging.core.io.utility import get_file_extension, get_prefix, find_images, find_log, find_180deg_proj
from mantidimaging.core.utility.data_containers import LoadingParameters, ImageParameters
from mantidimaging.gui.windows.load_dialog.field import Field

if TYPE_CHECKING:
    from mantidimaging.gui.windows.load_dialog import MWLoadDialog  # pragma: no cover
logger = getLogger(__name__)


class Notification(Enum):
    UPDATE_ALL_FIELDS = auto()
    UPDATE_FLAT_OR_DARK = auto()
    UPDATE_SINGLE_FILE = auto()
    UPDATE_SAMPLE_LOG = auto()


class LoadPresenter:
    view: 'MWLoadDialog'

    def __init__(self, view: 'MWLoadDialog'):
        self.view = view
        self.image_format = ''
        self.single_mem = 0
        self.last_file_info: Optional[FileInformation] = None
        self.dtype = '32'

    def notify(self, n: Notification, **baggage):
        try:
            if n == Notification.UPDATE_ALL_FIELDS:
                self.do_update_sample()
            elif n == Notification.UPDATE_FLAT_OR_DARK:
                self.do_update_flat_or_dark(**baggage)
            elif n == Notification.UPDATE_SINGLE_FILE:
                self.do_update_single_file(**baggage)
            elif n == Notification.UPDATE_SAMPLE_LOG:
                self.do_update_sample_log(**baggage)
        except RuntimeError as err:
            self.view.show_error(str(err), traceback.format_exc())

    def do_update_sample(self):
        """
        Updates the memory usage and the indices in the dialog.
        """
        selected_file = self.view.select_file("Sample")
        if not selected_file:
            return False

        self.view.sample.path = selected_file
        self.view.sample.widget.setExpanded(True)

        sample_filename = self.view.sample.file()
        self.image_format = get_file_extension(sample_filename)

        filename = self.view.sample.path_text()
        dirname = self.view.sample.directory()
        try:
            self.last_file_info = read_in_file_information(dirname,
                                                           in_prefix=get_prefix(filename),
                                                           in_format=self.image_format)
        except Exception as e:
            getLogger(__name__).error(f"Failed to read file {sample_filename} {e}")
            self.view.show_error("Failed to read this file. See log for details.", traceback.format_exc())
            self.last_file_info = None
            return

        sample_dirname = Path(dirname)

        self.view.flat_before.set_images(
            find_images(sample_dirname,
                        "Flat",
                        suffix="Before",
                        look_without_suffix=True,
                        image_format=self.image_format,
                        logger=logger))
        self.view.flat_after.set_images(
            find_images(sample_dirname, "Flat", suffix="After", image_format=self.image_format, logger=logger))
        self.view.dark_before.set_images(
            find_images(sample_dirname,
                        "Dark",
                        suffix="Before",
                        look_without_suffix=True,
                        image_format=self.image_format,
                        logger=logger))
        self.view.dark_after.set_images(
            find_images(sample_dirname, "Dark", suffix="After", image_format=self.image_format, logger=logger))
        self.view.proj_180deg.path = find_180deg_proj(sample_dirname, self.image_format, logger)

        try:
            self.set_sample_log(self.view.sample_log, sample_dirname, self.view.sample.directory(),
                                self.last_file_info.filenames)
        except RuntimeError as err:
            self.view.show_error(str(err), traceback.format_exc())

        self.view.sample_log.use = False

        self.view.flat_before_log.path = find_log(sample_dirname, self.view.flat_before.directory(), logger)
        self.view.flat_before_log.use = False

        self.view.flat_after_log.path = find_log(sample_dirname, self.view.flat_after.directory(), logger)
        self.view.flat_after_log.use = False

        self.view.images_are_sinograms.setChecked(self.last_file_info.sinograms)

        self.view.sample.update_indices(self.last_file_info.shape[0])
        self.view.sample.update_shape(self.last_file_info.shape[1:])

    def do_update_flat_or_dark(self, field: Field, name: str, suffix: str):
        selected_file = self.view.select_file(name)
        if not selected_file:
            return
        selected_dir = Path(os.path.dirname(selected_file))
        field.set_images(find_images(selected_dir, name, suffix, image_format=self.image_format, logger=logger))

    def get_parameters(self) -> LoadingParameters:
        lp = LoadingParameters()
        sample_log = self.view.sample_log.path_text() if self.view.sample_log.use.isChecked() else None
        lp.sample = ImageParameters(input_path=self.view.sample.directory(),
                                    format=self.image_format,
                                    prefix=get_prefix(self.view.sample.path_text()),
                                    indices=self.view.sample.indices,
                                    log_file=sample_log)

        lp.name = self.view.sample.file()
        lp.pixel_size = self.view.pixelSize.value()

        if self.view.flat_before.use.isChecked() and self.view.flat_before.path_text() != "":
            flat_before_log = self.view.flat_before_log.path_text() if self.view.flat_before_log.use.isChecked() \
                else None
            lp.flat_before = ImageParameters(input_path=self.view.flat_before.directory(),
                                             prefix=get_prefix(self.view.flat_before.path_text()),
                                             format=self.image_format,
                                             log_file=flat_before_log)

        if self.view.flat_after.use.isChecked() and self.view.flat_after.path_text() != "":
            flat_after_log = self.view.flat_after_log.path_text() if self.view.flat_after_log.use.isChecked() \
                else None
            lp.flat_after = ImageParameters(input_path=self.view.flat_after.directory(),
                                            prefix=get_prefix(self.view.flat_after.path_text()),
                                            format=self.image_format,
                                            log_file=flat_after_log)

        if self.view.dark_before.use.isChecked() and self.view.dark_before.path_text() != "":
            lp.dark_before = ImageParameters(input_path=self.view.dark_before.directory(),
                                             prefix=get_prefix(self.view.dark_before.path_text()),
                                             format=self.image_format)

        if self.view.dark_after.use.isChecked() and self.view.dark_after.path_text() != "":
            lp.dark_after = ImageParameters(input_path=self.view.dark_after.directory(),
                                            prefix=get_prefix(self.view.dark_after.path_text()),
                                            format=self.image_format)

        if self.view.proj_180deg.use.isChecked() and self.view.proj_180deg.path_text() != "":
            lp.proj_180deg = ImageParameters(input_path=self.view.proj_180deg.directory(),
                                             prefix=os.path.splitext(self.view.proj_180deg.path_text())[0],
                                             format=self.image_format)

        lp.dtype = self.view.pixel_bit_depth.currentText()
        lp.sinograms = self.view.images_are_sinograms.isChecked()
        lp.pixel_size = self.view.pixelSize.value()

        return lp

    def _update_field_action(self, field: Field, file_name):
        if file_name is not None:
            field.path = file_name
            field.use = True  # type: ignore

    def do_update_single_file(self, field: Field, name: str, is_image_file: bool):
        file_name = self.view.select_file(name, is_image_file)
        if file_name is None:
            return
        self._update_field_action(field, file_name)

    def do_update_sample_log(self, field: Field, name: str, is_image_file: bool):
        if self.last_file_info is None:
            raise RuntimeError("Please select sample data to be loaded first!")
        file_name = self.view.select_file(name, is_image_file)

        # this is set when the user selects sample data
        self.ensure_sample_log_consistency(field, file_name, self.last_file_info.filenames)

    def ensure_sample_log_consistency(self, field: Field, file_name, image_filenames):
        if file_name is None or file_name == "":
            return

        log = load_log(file_name)
        log.raise_if_angle_missing(image_filenames)
        self._update_field_action(field, file_name)

    def set_sample_log(self, sample_log: Field, sample_dirname, log_name, image_filenames):
        sample_log_filepath = find_log(sample_dirname, log_name, logger)
        self.ensure_sample_log_consistency(sample_log, sample_log_filepath, image_filenames)
        sample_log.path = sample_log_filepath
