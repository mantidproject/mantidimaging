import os
import traceback
from enum import auto, Enum
from logging import getLogger
from pathlib import Path
from typing import TYPE_CHECKING, List

from mantidimaging.core.io.loader import read_in_shape
from mantidimaging.core.io.utility import get_file_extension, get_prefix, get_file_names
from mantidimaging.gui.windows.main.load_dialog.field import Field

if TYPE_CHECKING:
    from mantidimaging.gui.windows.main.load_dialog.view import MWLoadDialog
logger = getLogger(__name__)


class Notification(Enum):
    UPDATE_ALL_FIELDS = auto()
    UPDATE_OTHER = auto()
    # UPDATE_EXPECTED_MEM_USAGE = auto()


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
        elif n == Notification.UPDATE_OTHER:
            self.do_update_other(**baggage)
        # elif n == Notification.UPDATE_EXPECTED_MEM_USAGE:
        #     self.do_update_expected_memory_usage()

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
            self.last_shape, sinograms = read_in_shape(dirname, in_prefix=get_prefix(filename),
                                                       in_format=self.image_format)
        except Exception as e:
            getLogger(__name__).error(f"Failed to read file {sample_filename} {e}")
            self.view.show_error("Failed to read this file. See log for details.",
                                 traceback.format_exc())
            self.last_shape = (0, 0, 0)
            sinograms = False

        sample_dirname = Path(dirname)

        self.view.flat.set_images(self._find_images(sample_dirname, "Flat"))
        self.view.dark.set_images(self._find_images(sample_dirname, "Dark"))
        self.view.proj_180deg.path = self._find_180deg_proj(sample_dirname)
        self.view.sample_log.path = self._find_log(sample_dirname, self.view.sample.directory())
        self.view.flat_log.path = self._find_log(sample_dirname, self.view.flat.directory())

        self.view.images_are_sinograms.setChecked(sinograms)

        self.view.sample.update_indices(self.last_shape[0])
        self.view.sample.update_shape(self.last_shape[1:])

    def _find_images(self, sample_dirname: Path, type: str) -> List[str]:
        # same folder
        try:
            return get_file_names(sample_dirname.absolute(), self.image_format, prefix=f"*{type}")
        except RuntimeError:
            logger.info(f"Could not find {type} files in {sample_dirname.absolute()}")

        # look into different directories 1 level above
        dirs = [f"{type.lower()}", type, f"{type}_After", f"{type}_Before"]

        for d in dirs:
            expected_folder_path = sample_dirname / ".." / d
            try:
                return get_file_names(expected_folder_path.absolute(), self.image_format)
            except RuntimeError:
                logger.info(f"Could not find {type} files in {expected_folder_path.absolute()}")

        return []

    # def do_update_expected_memory_usage(self):
    #     self._update_expected_mem_usage()

    def _find_180deg_proj(self, sample_dirname: Path):
        expected_path = sample_dirname / '..' / '180deg'
        try:
            return get_file_names(expected_path.absolute(), self.image_format)[0]
        except RuntimeError:
            logger.info(f"Could not find 180 degree projection in {expected_path}")
        return ""

    def _find_log(self, dirname: Path, log_name: str):
        expected_path = dirname / '..'
        try:
            return get_file_names(expected_path.absolute(), "txt", prefix=log_name)[0]
        except RuntimeError:
            logger.info(f"Could not find a log file for {log_name} in {dirname}")
        return ""

    def do_update_other(self, field: Field, name: str):
        selected_file = self.view.select_file(name)
        if not selected_file:
            return
        selected_dir = Path(os.path.dirname(selected_file))
        field.set_images(self._find_images(selected_dir, name))
