# Copyright (C) 2023 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

import os
import traceback
from logging import getLogger
from pathlib import Path
from typing import TYPE_CHECKING, Optional

from mantidimaging.core.io.filenames import FilenameGroup
from mantidimaging.core.io.loader import load_log
from mantidimaging.core.io.loader.loader import read_in_file_information, FileInformation, LoadingParameters, \
    ImageParameters
from mantidimaging.core.io.utility import (get_file_extension, get_prefix, find_images, find_log_for_image,
                                           find_180deg_proj)
from mantidimaging.core.utility.data_containers import FILE_TYPES, log_for_file_type
from mantidimaging.gui.windows.image_load_dialog.field import Field

if TYPE_CHECKING:
    from mantidimaging.gui.windows.image_load_dialog import ImageLoadDialog  # pragma: no cover

logger = getLogger(__name__)


class LoadPresenter:
    view: 'ImageLoadDialog'

    def __init__(self, view: 'ImageLoadDialog'):
        self.view = view
        self.image_format = ''
        self.single_mem = 0
        self.last_file_info: Optional[FileInformation] = None
        self.dtype = '32'

    def do_update_field(self, field: Field) -> None:
        name = field.file_info.fname
        is_image_file = field.file_info.mode != "log"
        selected_file = self.view.select_file(name, is_image_file)

        if field.file_info.mode == "sample":
            self.do_update_sample(selected_file)
        elif field.file_info.mode == "images":
            self.do_update_flat_or_dark(field, selected_file)
        elif field.file_info.fname == "Sample Log":
            self.do_update_sample_log(field, selected_file)
        elif field.file_info.mode in ["log", "180"]:
            self.do_update_single_file(field, selected_file)

    def do_update_sample(self, selected_file: Optional[str]) -> None:
        """
        Updates the memory usage and the indices in the dialog.
        """
        if not selected_file:
            self.view.ok_button.setEnabled(False)
            return

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

        for file_info in FILE_TYPES:
            if file_info.mode == "images":
                field = self.view.fields[file_info.fname]
                images = find_images(sample_dirname,
                                     file_info.tname,
                                     suffix=file_info.suffix,
                                     look_without_suffix=file_info.suffix == "Before",
                                     image_format=self.image_format)
                field.set_images(images)
            elif file_info.mode == "180":
                field = self.view.fields[file_info.fname]
                field.path = find_180deg_proj(sample_dirname, self.image_format)

        try:
            self.set_sample_log(self.view.fields["Sample Log"], self.last_file_info.filenames)
        except RuntimeError as err:
            self.view.show_error(str(err), traceback.format_exc())

        self.view.fields["Sample Log"].use = False

        for pos in ["Before", "After"]:
            flat_path = self.view.fields[f"Flat {pos}"].path_text()
            if flat_path:
                log_path = find_log_for_image(Path(flat_path))
                if log_path:
                    self.view.fields[f"Flat {pos} Log"].path = log_path
                    self.view.fields[f"Flat {pos} Log"].use = False

        self.view.images_are_sinograms.setChecked(self.last_file_info.sinograms)

        self.view.sample.update_indices(self.last_file_info.shape[0])
        self.view.sample.update_shape(self.last_file_info.shape[1:])
        self.view.enable_preview_all_buttons()
        self.view.ok_button.setEnabled(True)

    def do_update_flat_or_dark(self, field: Field, selected_file: Optional[str]) -> None:
        suffix = field.file_info.suffix
        if not selected_file:
            return
        selected_dir = Path(os.path.dirname(selected_file))
        images = find_images(selected_dir, field.file_info.fname, suffix, image_format=self.image_format)
        if not images:
            base_name = os.path.basename(selected_file).rpartition("_")[0]
            images = find_images(selected_dir, base_name, "", image_format=self.image_format)
        field.set_images(images)

    def get_parameters(self) -> LoadingParameters:
        """
        Gather information from the dialog into a LoadingParameters
        """
        loading_param = LoadingParameters()
        for file_type in FILE_TYPES:
            field = self.view.fields[file_type.fname]
            if not field.use.isChecked() or field.path_text() == "":
                continue
            file_group = FilenameGroup.from_file(Path(field.path_text()))
            file_group.find_all_files()
            image_param = ImageParameters(file_group)

            if file_type in log_for_file_type:
                log_field = self.view.fields[log_for_file_type[file_type].fname]
                if log_field.use.isChecked():
                    image_param.log_file = Path(log_field.path_text())

            if file_type == FILE_TYPES.SAMPLE:
                image_param.indices = field.indices

            loading_param.image_stacks[file_type] = image_param

        loading_param.name = self.view.fields[FILE_TYPES.SAMPLE.fname].file()
        loading_param.pixel_size = self.view.pixelSize.value()
        loading_param.dtype = self.view.pixel_bit_depth.currentText()
        loading_param.sinograms = self.view.images_are_sinograms.isChecked()
        return loading_param

    def _update_field_action(self, field: Field, file_name) -> None:
        if file_name is not None:
            field.path = file_name
            field.use = True  # type: ignore

    def do_update_single_file(self, field: Field, file_name: Optional[str]) -> None:
        if file_name is None:
            return
        self._update_field_action(field, file_name)

    def do_update_sample_log(self, field: Field, file_name: Optional[str]) -> None:
        if self.last_file_info is None:
            raise RuntimeError("Please select sample data to be loaded first!")

        # this is set when the user selects sample data
        if file_name:
            self.ensure_sample_log_consistency(field, file_name, self.last_file_info.filenames)

    def ensure_sample_log_consistency(self, field: Field, file_name: str, image_filenames: list[str]) -> None:
        if file_name is None or file_name == "":
            return

        log = load_log(Path(file_name))
        log.raise_if_angle_missing(image_filenames)
        self._update_field_action(field, file_name)

    def set_sample_log(self, sample_log: Field, image_filenames: list[str]) -> None:
        sample_log_filepath = find_log_for_image(Path(image_filenames[0]))
        if sample_log_filepath:
            self.ensure_sample_log_consistency(sample_log, str(sample_log_filepath), image_filenames)
            sample_log.path = sample_log_filepath
