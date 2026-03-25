# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

from enum import Enum, auto
from logging import getLogger
from pathlib import Path
from typing import TYPE_CHECKING

from mantidimaging.core.io.filenames import FilenameGroup
from mantidimaging.core.io.loader import load_log
from mantidimaging.core.io.loader.loader import LoadingParameters, ImageParameters, read_image_dimensions
from mantidimaging.core.utility.data_containers import FILE_TYPES, log_for_file_type, shuttercounts_for_file_type
from mantidimaging.gui.windows.image_load_dialog.field import Field

if TYPE_CHECKING:
    from mantidimaging.gui.windows.image_load_dialog import ImageLoadDialog  # pragma: no cover

logger = getLogger(__name__)


class _LogScenario(Enum):
    """
    Relationship between log entry count and the sample projection count.

    MATCH: log == slice == full stack; normal full-stack validation.
    FULL_STACK_NARROWED: log == full stack, slice < full stack; silent accept — loader slices angles to match.
    PARTIAL_SLICE_MATCH: log == slice < full stack; warn — angles may not correspond to the selected images.
    PARTIAL_BETWEEN: slice < log < full stack; warn — ambiguous match, angles may not correspond.
    MISMATCH: log count matches neither slice nor full stack; error.
    """
    MATCH = auto()
    FULL_STACK_NARROWED = auto()
    PARTIAL_SLICE_MATCH = auto()
    PARTIAL_BETWEEN = auto()
    MISMATCH = auto()


class LoadPresenter:
    view: ImageLoadDialog
    sample_fg: FilenameGroup | None = None

    def __init__(self, view: ImageLoadDialog):
        self.view = view
        self.image_format = ''
        self.single_mem = 0
        self.dtype = '32'

    def do_update_field(self, field: Field) -> None:
        """
        Called when user clicks select button.

        Does nothing if the select file dialog is canceled.
        """
        name = field.file_info.fname
        is_image_file = field.file_info.mode not in ["log", "ShutterCount"]
        selected_file = self.view.select_file(name, is_image_file)
        if selected_file is None:  # When select file is canceled
            return

        if field.file_info.mode == "sample":
            self.do_update_sample(selected_file)
        elif field.file_info.mode == "images":
            self.do_update_flat_or_dark(field, selected_file)
        elif field.file_info.fname == "Sample Log":
            self.do_update_sample_log(field, selected_file)
        elif field.file_info.mode in ["Sample Shutter Counts", "ShutterCount"]:
            self.do_update_shutter_counts(field, selected_file)
        elif field.file_info.mode in ["log", "180"]:
            self._update_field_action(field, selected_file)

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
            if file_info.mode in ["images", "180", "log"]:
                related_group = sample.find_related(file_info)
                if related_group:
                    self.update_field_with_filegroup(file_info, related_group)

    def update_field_with_filegroup(self, file_info: FILE_TYPES, file_group: FilenameGroup) -> None:
        """
        Update the field with the given file group by finding all files in the group and setting them in the field.

        :param file_info (FILE_TYPES): The file information.
        :param file_group (FilenameGroup): The file group containing the files.

        :return None
        """
        file_group.find_all_files()  # find all files in the group to register related file parsers
        self.view.fields[file_info.fname].set_images(list(file_group.all_files()))
        self._update_field(file_info, file_group, log_for_file_type, 'find_log_file', 'log_path')

        self._update_field(file_info, file_group, shuttercounts_for_file_type, 'find_shutter_count_file',
                           'shutter_count_path')

    def _update_field(self, file_info, file_group, file_type_dict, find_file_method, file_path_attr):
        if file_info in file_type_dict:
            getattr(file_group, find_file_method)()
            if getattr(file_group, file_path_attr):
                field = self.view.fields[file_type_dict[file_info].fname]
                field.path = getattr(file_group, file_path_attr)
                field.use = True

    def do_update_shutter_counts(self, field: Field, selected_file: str) -> None:
        """
        Updates the shutter counts for the selected file.

        :param  field (Field): The field to update with the shutter counts.
        :param  selected_file (str): The path of the selected file.

        :return None
        """
        filename_group = FilenameGroup.from_file(Path(selected_file))
        field.set_images(list(filename_group.all_files()))
        self._update_field_action(field, selected_file)
        self.ensure_sample_shuttercount_consistency(field, selected_file)

    def ensure_sample_shuttercount_consistency(self, field: Field, file_name: str) -> None:
        if file_name is None or file_name == "":
            return
        self._update_field_action(field, file_name)

    def do_update_flat_or_dark(self, field: Field, selected_file: str) -> None:
        """
        Update the field with the images from the selected file.
        :param  field (Field): The field to update.
        :param  selected_file (str): The path of the selected file.
        :return None
        """
        filename_group = FilenameGroup.from_file(Path(selected_file))
        filename_group.find_all_files()
        field.set_images(list(filename_group.all_files()))

    def get_parameters(self) -> LoadingParameters:
        """
        Get the loading parameters for the selected sample.
        :return LoadingParameters: The loading parameters for the selected sample.
        :raises  RuntimeError: If no sample is selected.
        """
        sample_field = self.view.fields[FILE_TYPES.SAMPLE.fname]
        if sample_field.path is None:
            raise RuntimeError("No sample selected")

        loading_param = LoadingParameters()
        for file_type in FILE_TYPES:
            self._update_loading_param(file_type, loading_param)

        loading_param.name = sample_field.path.name
        loading_param.pixel_size = self.view.pixelSize.value()
        loading_param.dtype = self.view.pixel_bit_depth.currentText()
        loading_param.sinograms = self.view.images_are_sinograms.isChecked()
        return loading_param

    def _update_loading_param(self, file_type: FILE_TYPES, loading_param: LoadingParameters):
        """
        Update the loading parameters for a specific file type.
        :param  file_type: The type of the file being loaded.
        :param  loading_param: The loading parameters object.
        :return None
        """
        if file_type.mode in ["log", "ShutterCount"]:
            return

        field = self.view.fields[file_type.fname]
        if not field.use.isChecked() or field.path is None:
            return

        file_group = FilenameGroup.from_file(field.path)
        file_group.find_all_files()
        image_param = ImageParameters(file_group)

        if file_type in log_for_file_type:
            self._update_image_param(file_type, image_param, log_for_file_type, 'log_file')
        if file_type in shuttercounts_for_file_type:
            self._update_image_param(file_type, image_param, shuttercounts_for_file_type, 'shutter_count_file')

        if file_type == FILE_TYPES.SAMPLE:
            image_param.indices = field.indices

        loading_param.image_stacks[file_type] = image_param

    def _update_image_param(self, file_type: FILE_TYPES, image_param: ImageParameters, file_type_dict: dict,
                            attr_name: str) -> None:
        """
        Update the image parameter based on the selected file type.
        :param  file_type: The selected file type.
        :param  image_param (ImageParam): The image parameter object to update.
        :param  file_type_dict: A dictionary mapping file types to their corresponding attributes.
        :param  attr_name: The name of the attribute to update in the image parameter.
        :return None
        """
        field = self.view.fields[file_type_dict[file_type].fname]
        if field.use.isChecked():
            setattr(image_param, attr_name, field.path)

    def _update_field_action(self, field: Field, file_name) -> None:
        if file_name is not None:
            field.path = Path(file_name)
            field.use = True  # type: ignore

    def do_update_sample_log(self, field: Field, file_name: str) -> None:
        """
        Update the sample log if a sample is set.
        Check log is consistent with sample and handle field updates.

        :param field: The log field in the load dialog to update.
        :param file_name: Path to the selected log file.
        """
        if self.sample_fg is None:
            raise RuntimeError("Please select sample data to be loaded first!")

        indices = self.view.fields[FILE_TYPES.SAMPLE.fname].indices
        full_stack_filenames = [file_path.name for file_path in self.sample_fg.all_files()]
        sample_names = full_stack_filenames[indices.start:indices.end:indices.step]
        if self.validate_sample_log(field, file_name, sample_names, full_stack_filenames):
            self._update_field_action(field, file_name)

    def validate_sample_log(self, field: Field, file_name: str, selected_filenames: list[str],
                            full_stack_filenames: list[str]) -> bool:
        """
        Validate that the log file is consistent with the images to be loaded.

        :param field: Log field in the load dialog to update.
        :param file_name: Path to the selected log file.
        :param selected_filenames: Filenames after index selection.
        :param full_stack_filenames: All filenames in the full stack.
        :return: True if the log is accepted, False if rejected.
        """
        if file_name is None or file_name == "":
            return False

        log = load_log(Path(file_name))
        scenario = self._classify_log_scenario(log.length, len(selected_filenames), len(full_stack_filenames))

        match scenario:
            case _LogScenario.MATCH:
                log.raise_if_angle_missing(selected_filenames)
                return True
            case _LogScenario.FULL_STACK_NARROWED:
                return True
            case _LogScenario.PARTIAL_SLICE_MATCH | _LogScenario.PARTIAL_BETWEEN:
                return self._warn_partial_log(field, log.length, len(selected_filenames), len(full_stack_filenames))
            case _LogScenario.MISMATCH:
                self._show_log_mismatch_error(log.length, len(selected_filenames), len(full_stack_filenames))
                field.clear()
                return False

    @staticmethod
    def _classify_log_scenario(log_length: int, slice_count: int, full_count: int) -> _LogScenario:
        """Classify the log/stack size relationship into one of various scenarios."""
        if log_length == full_count:
            return _LogScenario.FULL_STACK_NARROWED if slice_count < full_count else _LogScenario.MATCH
        if log_length == slice_count < full_count:
            return _LogScenario.PARTIAL_SLICE_MATCH
        if slice_count < log_length < full_count:
            return _LogScenario.PARTIAL_BETWEEN
        return _LogScenario.MISMATCH

    def _warn_partial_log(self, field: Field, log_length: int, slice_count: int, full_count: int) -> bool:
        """
        Show a confirmation dialog for scenarios FULL_STACK_NARROWED and PARTIAL_SLICE_MATCH.
        Returns True if the user confirms.
        Clears the field and returns False if the user declines.
        """
        if log_length == slice_count:
            detail = f"The current index selection of {slice_count} images matches the log size"
        else:
            detail = f"The log is larger than the current index selection of {slice_count} images"

        if not self.view.show_question_dialog(
                "Warning: Log size mismatch",
                f"The log file contains {log_length} entries, fewer than the full sample stack "
                f"({full_count} images). {detail}, but the projection angles may not correctly "
                f"correspond to the selected images.\n\n"
                f"Do you want to continue?"):
            field.clear()

            return False
        return True

    def _show_log_mismatch_error(self, log_length: int, slice_count: int, full_count: int) -> None:
        """
        Show an error dialog for a genuine log/stack mismatch.
        """
        if slice_count != full_count:
            stack_desc = (f"{slice_count} images in the selected index range "
                          f"and {full_count} images in the full stack")
        else:
            stack_desc = f"{full_count} images in the stack"

        self.view.show_error_dialog(f"Log size mismatch. Found {log_length} log entries but {stack_desc}. "
                                    f"The log file may not correspond to this sample stack.")
