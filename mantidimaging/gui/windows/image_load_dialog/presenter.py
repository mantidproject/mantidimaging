# Copyright (C) 2022 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later

import os
import traceback
from logging import getLogger
from pathlib import Path
from typing import TYPE_CHECKING, Optional, NamedTuple, Dict

from mantidimaging.core.io.loader import load_log
from mantidimaging.core.io.loader.loader import read_in_file_information, FileInformation
from mantidimaging.core.io.utility import (get_file_extension, get_prefix, find_images, find_log_for_image,
                                           find_180deg_proj)
from mantidimaging.core.utility.data_containers import LoadingParameters, ImageParameters
from mantidimaging.gui.windows.image_load_dialog.field import Field

if TYPE_CHECKING:
    from mantidimaging.gui.windows.image_load_dialog import ImageLoadDialog  # pragma: no cover

logger = getLogger(__name__)


class TypeInfo(NamedTuple):
    name: str
    suffix: str
    mode: str


FILE_TYPES: Dict[str, TypeInfo] = {
    "Sample": TypeInfo("Sample", "", "sample"),
    "Flat Before": TypeInfo("Flat", "Before", "images"),
    "Flat After": TypeInfo("Flat", "After", "images"),
    "Dark Before": TypeInfo("Dark", "Before", "images"),
    "Dark After": TypeInfo("Dark", "After", "images"),
    "180 degree": TypeInfo("180 degree", "", "180"),
    "Sample Log": TypeInfo("Sample Log", "", "log"),
    "Flat Before Log": TypeInfo("Flat Before Log", "", "log"),
    "Flat After Log": TypeInfo("Flat After Log", "", "log"),
}


class LoadPresenter:
    view: 'ImageLoadDialog'

    def __init__(self, view: 'ImageLoadDialog'):
        self.view = view
        self.image_format = ''
        self.single_mem = 0
        self.last_file_info: Optional[FileInformation] = None
        self.dtype = '32'

    def do_update_field(self, field: Field):
        if field.file_info.mode == "sample":
            self.do_update_sample()
        elif field.file_info.mode == "images":
            self.do_update_flat_or_dark(field)
        elif field.file_info.name == "Sample Log":
            self.do_update_sample_log(field)
        elif field.file_info.mode in ["log", "180"]:
            self.do_update_single_file(field)

    def do_update_sample(self):
        """
        Updates the memory usage and the indices in the dialog.
        """
        selected_file = self.view.select_file("Sample")
        if not selected_file:
            self.view.ok_button.setEnabled(False)
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

        for file_info_name, file_info in FILE_TYPES.items():
            if file_info.mode == "images":
                field = self.view.fields[file_info_name]
                images = find_images(sample_dirname,
                                     file_info.name,
                                     suffix=file_info.suffix,
                                     look_without_suffix="Before" in file_info_name,
                                     image_format=self.image_format,
                                     logger=logger)
                field.set_images(images)
            elif file_info.mode == "180":
                field = self.view.fields[file_info_name]
                field.path = find_180deg_proj(sample_dirname, self.image_format, logger)

        try:
            self.set_sample_log(self.view.fields["Sample Log"], self.last_file_info.filenames)
        except RuntimeError as err:
            self.view.show_error(str(err), traceback.format_exc())

        self.view.fields["Sample Log"].use = False

        for pos in ["Before", "After"]:
            self.view.fields[f"Flat {pos} Log"].path = find_log_for_image(self.view.fields[f"Flat {pos}"].path_text())
            self.view.fields[f"Flat {pos} Log"].use = False

        self.view.images_are_sinograms.setChecked(self.last_file_info.sinograms)

        self.view.sample.update_indices(self.last_file_info.shape[0])
        self.view.sample.update_shape(self.last_file_info.shape[1:])
        self.view.enable_preview_all_buttons()
        self.view.ok_button.setEnabled(True)

    def do_update_flat_or_dark(self, field: Field):
        name = field.file_info.name
        suffix = field.file_info.suffix
        selected_file = self.view.select_file(name)
        if not selected_file:
            return
        selected_dir = Path(os.path.dirname(selected_file))
        images = find_images(selected_dir, name, suffix, image_format=self.image_format, logger=logger)
        if not images:
            base_name = os.path.basename(selected_file).rpartition("_")[0]
            images = find_images(selected_dir, base_name, "", image_format=self.image_format, logger=logger)
        field.set_images(images)

    def get_parameters(self) -> LoadingParameters:
        lp = LoadingParameters()

        for image_group in [k for k, v in FILE_TYPES.items() if v.mode in ["images", "sample"]]:
            image_field = self.view.fields[image_group]
            if not image_field.use.isChecked() or image_field.path_text() == "":
                continue

            params = ImageParameters(input_path=image_field.directory(),
                                     format=self.image_format,
                                     prefix=get_prefix(image_field.path_text()))

            if image_group == "Sample":
                params.indices = image_field.indices

            if image_group + " Log" in self.view.fields:
                log_field = self.view.fields[image_group + " Log"]
                if log_field.use.isChecked():
                    params.log_file = Path(log_field.path_text())

            lp.set(image_group, params)

        field_180 = self.view.fields["180 degree"]
        if field_180.use.isChecked() and field_180.path_text() != "":
            lp.proj_180deg = ImageParameters(input_path=field_180.directory(),
                                             prefix=os.path.splitext(field_180.path_text())[0],
                                             format=self.image_format)

        lp.name = self.view.sample.file()
        lp.pixel_size = self.view.pixelSize.value()
        lp.dtype = self.view.pixel_bit_depth.currentText()
        lp.sinograms = self.view.images_are_sinograms.isChecked()
        lp.pixel_size = self.view.pixelSize.value()

        return lp

    def _update_field_action(self, field: Field, file_name):
        if file_name is not None:
            field.path = file_name
            field.use = True  # type: ignore

    def do_update_single_file(self, field: Field):
        name = field.file_info.name
        is_image_file = field.file_info.mode in ["image", "180"]
        file_name = self.view.select_file(name, is_image_file)
        if file_name is None:
            return
        self._update_field_action(field, file_name)

    def do_update_sample_log(self, field: Field):
        name = field.file_info.name
        if self.last_file_info is None:
            raise RuntimeError("Please select sample data to be loaded first!")
        file_name = self.view.select_file(name, False)

        # this is set when the user selects sample data
        self.ensure_sample_log_consistency(field, file_name, self.last_file_info.filenames)

    def ensure_sample_log_consistency(self, field: Field, file_name, image_filenames):
        if file_name is None or file_name == "":
            return

        log = load_log(file_name)
        log.raise_if_angle_missing(image_filenames)
        self._update_field_action(field, file_name)

    def set_sample_log(self, sample_log: Field, image_filenames):
        sample_log_filepath = find_log_for_image(Path(image_filenames[0]))
        self.ensure_sample_log_consistency(sample_log, sample_log_filepath, image_filenames)
        sample_log.path = sample_log_filepath
