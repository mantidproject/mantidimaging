# Copyright (C) 2023 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

from logging import getLogger
from pathlib import Path
from typing import TYPE_CHECKING, Optional

from mantidimaging.core.io.filenames import FilenameGroup
from mantidimaging.core.io.loader import load_log
from mantidimaging.core.io.loader.loader import LoadingParameters, ImageParameters, read_image_dimensions
from mantidimaging.core.io.utility import find_log_for_image
from mantidimaging.core.utility.data_containers import FILE_TYPES, log_for_file_type
from mantidimaging.gui.windows.image_load_dialog.field import Field

if TYPE_CHECKING:
    from mantidimaging.gui.windows.image_load_dialog import ImageLoadDialog  # pragma: no cover

logger = getLogger(__name__)


class LoadPresenter:
    view: 'ImageLoadDialog'
    sample_fg: Optional[FilenameGroup] = None

    def __init__(self, view: 'ImageLoadDialog'):
        self.view = view
        self.image_format = ''
        self.single_mem = 0
        self.dtype = '32'

    def do_update_field(self, field: Field) -> None:
        name = field.file_info.fname
        is_image_file = field.file_info.mode != "log"
        selected_file = self.view.select_file(name, is_image_file)
        if selected_file is None:
            # When select file is canceled
            return

        if field.file_info.mode == "sample":
            self.do_update_sample(selected_file)
        elif field.file_info.mode == "images":
            self.do_update_flat_or_dark(field, selected_file)
        elif field.file_info.fname == "Sample Log":
            self.do_update_sample_log(field, selected_file)
        elif field.file_info.mode in ["log", "180"]:
            self.do_update_single_file(field, selected_file)

    def do_update_sample(self, selected_file: str) -> None:
        """
        Updates the memory usage and the indices in the dialog.
        """
        sample_field = self.view.fields[FILE_TYPES.SAMPLE.fname]

        sample = FilenameGroup.from_file(Path(selected_file))
        self.sample_fg = sample
        self.update_field_with_filegroup(FILE_TYPES.SAMPLE, sample)

        sample_field.widget.setExpanded(True)
        sample_shape = read_image_dimensions(Path(selected_file))
        self.view.sample.update_indices(len(sample.all_indexes))
        self.view.sample.update_shape(sample_shape)
        self.view.enable_preview_all_buttons()
        self.view.ok_button.setEnabled(True)

        for file_info in FILE_TYPES:
            if file_info.mode in ["images", "180"]:
                related_group = sample.find_related(file_info)
                if related_group:
                    self.update_field_with_filegroup(file_info, related_group)

    def update_field_with_filegroup(self, file_info: FILE_TYPES, file_group: FilenameGroup):
        file_group.find_all_files()
        file_list = list(file_group.all_files())
        self.view.fields[file_info.fname].set_images(file_list)

        if file_info in log_for_file_type:
            file_group.find_log_file()

            if file_group.log_path:
                log_field = self.view.fields[log_for_file_type[file_info].fname]
                log_field.path = file_group.log_path
                log_field.use = False

    def do_update_flat_or_dark(self, field: Field, selected_file: str) -> None:
        fg = FilenameGroup.from_file(Path(selected_file))
        fg.find_all_files()
        field.set_images(list(fg.all_files()))

    def get_parameters(self) -> LoadingParameters:
        """
        Gather information from the dialog into a LoadingParameters
        """
        sample_field = self.view.fields[FILE_TYPES.SAMPLE.fname]
        if sample_field.path is None:
            raise RuntimeError("No sample selected")

        loading_param = LoadingParameters()
        for file_type in FILE_TYPES:
            field = self.view.fields[file_type.fname]
            if not field.use.isChecked() or field.path is None:
                continue
            file_group = FilenameGroup.from_file(field.path)
            file_group.find_all_files()
            image_param = ImageParameters(file_group)

            if file_type in log_for_file_type:
                log_field = self.view.fields[log_for_file_type[file_type].fname]
                if log_field.use.isChecked():
                    image_param.log_file = log_field.path

            if file_type == FILE_TYPES.SAMPLE:
                image_param.indices = field.indices

            loading_param.image_stacks[file_type] = image_param

        loading_param.name = sample_field.path.name
        loading_param.pixel_size = self.view.pixelSize.value()
        loading_param.dtype = self.view.pixel_bit_depth.currentText()
        loading_param.sinograms = self.view.images_are_sinograms.isChecked()
        return loading_param

    def _update_field_action(self, field: Field, file_name) -> None:
        if file_name is not None:
            field.path = Path(file_name)
            field.use = True  # type: ignore

    def do_update_single_file(self, field: Field, file_name: str) -> None:
        self._update_field_action(field, file_name)

    def do_update_sample_log(self, field: Field, file_name: str) -> None:
        if self.sample_fg is None:
            raise RuntimeError("Please select sample data to be loaded first!")

        # this is set when the user selects sample data
        sample_names = [p.name for p in self.sample_fg.all_files()]
        self.ensure_sample_log_consistency(field, file_name, sample_names)

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
