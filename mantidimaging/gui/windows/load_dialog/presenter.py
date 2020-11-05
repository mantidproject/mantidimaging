import os
import traceback
from enum import auto, Enum
from logging import getLogger
from pathlib import Path
from typing import TYPE_CHECKING, List

from mantidimaging.core.io.loader import read_in_shape
from mantidimaging.core.io.utility import get_file_extension, get_prefix, get_file_names
from mantidimaging.core.utility.data_containers import LoadingParameters, ImageParameters
from mantidimaging.gui.windows.load_dialog.field import Field

if TYPE_CHECKING:
    from mantidimaging.gui.windows.load_dialog import MWLoadDialog
logger = getLogger(__name__)


class Notification(Enum):
    UPDATE_ALL_FIELDS = auto()
    UPDATE_FLAT_OR_DARK = auto()
    UPDATE_SINGLE_FILE = auto()


class LoadPresenter:
    view: 'MWLoadDialog'

    def __init__(self, view: 'MWLoadDialog'):
        self.view = view
        self.image_format = ''
        self.single_mem = 0
        self.last_shape = (0, 0, 0)
        self.dtype = '32'

    def notify(self, n: Notification, **baggage):
        if n == Notification.UPDATE_ALL_FIELDS:
            self.do_update_sample()
        elif n == Notification.UPDATE_FLAT_OR_DARK:
            self.do_update_flat_or_dark(**baggage)
        elif n == Notification.UPDATE_SINGLE_FILE:
            self.do_update_single_file(**baggage)

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
            self.last_shape, sinograms = read_in_shape(dirname,
                                                       in_prefix=get_prefix(filename),
                                                       in_format=self.image_format)
        except Exception as e:
            getLogger(__name__).error(f"Failed to read file {sample_filename} {e}")
            self.view.show_error("Failed to read this file. See log for details.", traceback.format_exc())
            self.last_shape = (0, 0, 0)
            sinograms = False

        sample_dirname = Path(dirname)

        self.view.flat_before.set_images(self._find_images(sample_dirname, "Flat", suffix="Before"))
        self.view.flat_after.set_images(self._find_images(sample_dirname, "Flat", suffix="After"))
        self.view.dark_before.set_images(self._find_images(sample_dirname, "Dark", suffix="Before"))
        self.view.dark_after.set_images(self._find_images(sample_dirname, "Dark", suffix="After"))
        self.view.proj_180deg.path = self._find_180deg_proj(sample_dirname)

        self.view.sample_log.path = self._find_log(sample_dirname, self.view.sample.directory())
        self.view.sample_log.use = False

        self.view.flat_before_log.path = self._find_log(sample_dirname, self.view.flat_before.directory())
        self.view.flat_before_log.use = False

        self.view.flat_after_log.path = self._find_log(sample_dirname, self.view.flat_after.directory())
        self.view.flat_after_log.use = False

        self.view.images_are_sinograms.setChecked(sinograms)

        self.view.sample.update_indices(self.last_shape[0])
        self.view.sample.update_shape(self.last_shape[1:])

    def _find_images(self, sample_dirname: Path, type: str, suffix: str = None) -> List[str]:
        # same folder
        try:
            if suffix is None or suffix != "After":
                return get_file_names(sample_dirname.absolute(), self.image_format, prefix=f"*{type}")
        except RuntimeError:
            logger.info(f"Could not find {type} files in {sample_dirname.absolute()}")
            if suffix is not None:
                try:
                    return get_file_names(sample_dirname.absolute(), self.image_format, prefix=f"*{type}_{suffix}")
                except RuntimeError:
                    logger.info(f"Could not find {type}_{suffix} files in {sample_dirname.absolute()}")

        # look into different directories 1 level above
        dirs = [type + " " + suffix, type + "_" + suffix, f"{type.lower()}", type]

        for d in dirs:
            expected_folder_path = sample_dirname / ".." / d
            try:
                return get_file_names(expected_folder_path.absolute(), self.image_format)
            except RuntimeError:
                logger.info(f"Could not find {type} files in {expected_folder_path.absolute()}")

        return []

    def _find_180deg_proj(self, sample_dirname: Path):
        expected_path = sample_dirname / '..' / '180deg'
        try:
            return get_file_names(expected_path.absolute(), self.image_format)[0]
        except RuntimeError:
            logger.info(f"Could not find 180 degree projection in {expected_path}")
        return ""

    @staticmethod
    def _find_log(dirname: Path, log_name: str):
        expected_path = dirname / '..'
        try:
            return get_file_names(expected_path.absolute(), "txt", prefix=log_name)[0]
        except RuntimeError:
            logger.info(f"Could not find a log file for {log_name} in {dirname}")
        return ""

    def do_update_flat_or_dark(self, field: Field, name: str):
        selected_file = self.view.select_file(name)
        if not selected_file:
            return
        selected_dir = Path(os.path.dirname(selected_file))
        field.set_images(self._find_images(selected_dir, name))

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

    def do_update_single_file(self, field, name, image_file):
        try:
            file_name = self.view.select_file(name, image_file)
        except RuntimeError:
            logger.info(f"Could not find the {name} file")
            return

        if file_name is not None:
            field.path = file_name
            field.use = True
