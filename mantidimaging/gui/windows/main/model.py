# Copyright (C) 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
import glob
import os
import uuid
from collections import namedtuple
from logging import getLogger
from pathlib import Path
from typing import Any, Dict, List, Optional

from PyQt5.QtWidgets import QDockWidget

from core.io.loader import load_log, read_in_file_information
from core.io.utility import find_images, find_log, get_prefix
from mantidimaging.core.data import Images
from mantidimaging.core.data.dataset import Dataset
from mantidimaging.core.io import loader, saver
from mantidimaging.core.utility.data_containers import LoadingParameters, ProjectionAngles, ImageParameters
from mantidimaging.gui.windows.stack_visualiser import StackVisualiserView

StackId = namedtuple('StackId', ['id', 'name'])
logger = getLogger(__name__)


class MainWindowModel(object):
    def __init__(self):
        super(MainWindowModel, self).__init__()

        self.active_stacks: Dict[uuid.UUID, QDockWidget] = {}

    def do_load_stack(self, parameters: LoadingParameters, progress):
        ds = Dataset(loader.load_p(parameters.sample, parameters.dtype, progress))
        ds.sample._is_sinograms = parameters.sinograms
        ds.sample.pixel_size = parameters.pixel_size

        if parameters.sample.log_file:
            ds.sample.log_file = loader.load_log(parameters.sample.log_file)

        if parameters.flat_before:
            ds.flat_before = loader.load_p(parameters.flat_before, parameters.dtype, progress)
            if parameters.flat_before.log_file:
                ds.flat_before.log_file = loader.load_log(parameters.flat_before.log_file)
        if parameters.flat_after:
            ds.flat_after = loader.load_p(parameters.flat_after, parameters.dtype, progress)
            if parameters.flat_after.log_file:
                ds.flat_after.log_file = loader.load_log(parameters.flat_after.log_file)

        if parameters.dark_before:
            ds.dark_before = loader.load_p(parameters.dark_before, parameters.dtype, progress)
        if parameters.dark_after:
            ds.dark_after = loader.load_p(parameters.dark_after, parameters.dtype, progress)

        if parameters.proj_180deg:
            ds.sample.proj180deg = loader.load_p(parameters.proj_180deg, parameters.dtype, progress)

        return ds

    @staticmethod
    def load_stack(file_path: str, progress) -> Images:
        return loader.load_stack(file_path, progress)

    def do_saving(self, stack_uuid, output_dir, name_prefix, image_format, overwrite, pixel_depth, progress):
        svp = self.get_stack_visualiser(stack_uuid).presenter
        filenames = saver.save(svp.images,
                               output_dir=output_dir,
                               name_prefix=name_prefix,
                               overwrite_all=overwrite,
                               out_format=image_format,
                               pixel_depth=pixel_depth,
                               progress=progress)
        svp.images.filenames = filenames
        return True

    def create_name(self, filename):
        """
        Creates a suitable name for a newly loaded stack.
        """
        # Avoid file extensions in names
        filename = os.path.splitext(filename)[0]

        # Avoid duplicate names
        name = filename
        current_names = self._stack_names
        num = 1
        while name in current_names:
            num += 1
            name = f"{filename}_{num}"

        return name

    @property
    def stack_list(self) -> List[StackId]:
        stacks = [StackId(stack_id, widget.windowTitle()) for stack_id, widget in self.active_stacks.items()]
        return sorted(stacks, key=lambda x: x.name)

    @property
    def _stack_names(self) -> List[str]:
        return [stack.name for stack in self.stack_list]

    def add_stack(self, stack_visualiser: StackVisualiserView, dock_widget: 'QDockWidget'):
        stack_visualiser.uuid = uuid.uuid1()
        self.active_stacks[stack_visualiser.uuid] = dock_widget
        logger.debug(f"Active stacks: {self.active_stacks}")

    def get_stack(self, stack_uuid: uuid.UUID) -> QDockWidget:
        """
        :param stack_uuid: The unique ID of the stack that will be retrieved.
        :return The QDockWidget that contains the Stack Visualiser.
                For direct access to the Stack Visualiser widget use
                get_stack_visualiser
        """
        return self.active_stacks[stack_uuid]  # type:ignore

    def set_images_in_stack(self, stack_uuid: uuid.UUID, images: Images):
        stack = self.active_stacks[stack_uuid]
        if isinstance(stack, QDockWidget):
            stack: StackVisualiserView = stack.widget()  # type:ignore

        if not stack.presenter.images == images:
            stack.image_view.clear()
            stack.image_view.setImage(images.data)

            # Free previous images stack before reassignment
            stack.presenter.images = images

    def get_stack_by_name(self, search_name: str) -> Optional[QDockWidget]:
        for stack_id in self.stack_list:
            if stack_id.name == search_name:
                return self.get_stack(stack_id.id)
        return None

    def get_stack_by_images(self, images: Images) -> StackVisualiserView:
        for _, dock_widget in self.active_stacks.items():
            sv: StackVisualiserView = dock_widget.widget()  # type: ignore
            if images is sv.presenter.images:
                return sv
        raise RuntimeError(f"Did not find stack {images} in active stacks! "
                           f"Active stacks: {self.active_stacks.items()}")

    def get_stack_visualiser(self, stack_uuid: uuid.UUID) -> StackVisualiserView:
        """
        :param stack_uuid: The unique ID of the stack that will be retrieved.
        :return The Stack Visualiser widget that contains the data.
        """
        return self.active_stacks[stack_uuid].widget()  # type:ignore

    def get_all_stack_visualisers(self) -> List[StackVisualiserView]:
        return [stack.widget() for stack in self.active_stacks.values()]  # type:ignore

    def get_all_stack_visualisers_with_180deg_proj(self) -> List[StackVisualiserView]:
        return [
            stack.widget() for stack in self.active_stacks.values()  # type:ignore
            if stack.widget().presenter.images.has_proj180deg()
        ]

    def get_stack_history(self, stack_uuid: uuid.UUID) -> Optional[Dict[str, Any]]:
        return self.get_stack_visualiser(stack_uuid).presenter.images.metadata

    def do_remove_stack(self, stack_uuid: uuid.UUID) -> None:
        """
        Removes the stack from the active_stacks dictionary.

        :param stack_uuid: The unique ID of the stack that will be removed.
        """
        del self.active_stacks[stack_uuid]

    @property
    def have_active_stacks(self) -> bool:
        return len(self.active_stacks) > 0

    def add_log_to_sample(self, stack_name: str, log_file: str):
        stack_dock = self.get_stack_by_name(stack_name)
        if stack_dock is None:
            raise RuntimeError(f"Failed to get stack with name {stack_name}")

        stack: StackVisualiserView = stack_dock.widget()  # type: ignore
        log = loader.load_log(log_file)
        log.raise_if_angle_missing(stack.presenter.images.filenames)
        stack.presenter.images.log_file = log

    def add_180_deg_to_stack(self, stack_name, _180_deg_file):
        stack_dock = self.get_stack_by_name(stack_name)
        if stack_dock is None:
            raise RuntimeError(f"Failed to get stack with name {stack_name}")

        stack: StackVisualiserView = stack_dock.widget()  # type: ignore
        _180_deg = loader.load(file_names=[_180_deg_file])
        stack.presenter.images.proj180deg = _180_deg.sample
        return _180_deg

    def add_projection_angles_to_sample(self, stack_name: str, proj_angles: ProjectionAngles):
        stack_dock = self.get_stack_by_name(stack_name)
        if stack_dock is None:
            raise RuntimeError(f"Failed to get stack with name {stack_name}")

        stack: StackVisualiserView = stack_dock.widget()  # type: ignore
        images: Images = stack.presenter.images
        images.set_projection_angles(proj_angles)

    @staticmethod
    def find_first_file_that_is_possibly_a_sample(file_path: str) -> Optional[str]:
        # Grab all .tif or .tiff files
        possible_files = glob.glob(os.path.join(file_path, "**/*.tif*"), recursive=True)

        for possible_file in possible_files:
            lower_filename = os.path.basename(possible_file).lower()
            if "flat" not in lower_filename and "dark" not in lower_filename and "180" not in lower_filename:
                return possible_file

    @staticmethod
    def find_and_verify_sample_log(sample_directory: str, image_filenames):
        sample_log = find_log(dirname=Path(sample_directory), log_name=sample_directory)

        log = load_log(sample_log)
        log.raise_if_angle_missing(image_filenames)

        return sample_log

    def create_loading_parameters_for_file_path(self, file_path: str):
        sample_file = self.find_first_file_that_is_possibly_a_sample(file_path)
        if sample_file is None:
            return

        loading_parameters = LoadingParameters()
        _, image_format = os.path.splitext(sample_file)
        sample_directory = os.path.dirname(sample_file)
        last_file_info = read_in_file_information(sample_directory,
                                                  in_prefix=get_prefix(sample_file),
                                                  in_format=image_format)
        sample_log = self.find_and_verify_sample_log(sample_directory, last_file_info)

        loading_parameters.sample = ImageParameters(input_path=sample_directory,
                                                    format=image_format,
                                                    prefix=get_prefix(sample_file),
                                                    log_file=sample_log,
                                                    indices=last_file_info.shape[0])

        # Flat before
        flat_before_image = find_images(Path(sample_directory), "Flat", suffix="Before", look_without_suffix=True,
                                        image_format=image_format, logger=logger)[0]
        flat_before_directory = os.path.dirname(flat_before_image)
        flat_before_log = find_log(Path(sample_directory), flat_before_directory, logger)

        loading_parameters.flat_before = ImageParameters(input_path=flat_before_directory, format=image_format,
                                                         prefix=get_prefix(flat_before_image), log_file=flat_before_log)

        # Flat after
        flat_after_image = find_images(Path(sample_directory), "Flat", suffix="After",
                                       image_format=image_format, logger=logger)[0]
        flat_after_directory = os.path.dirname(flat_after_image)
        flat_after_log = find_log(Path(sample_directory), flat_after_directory, logger)

        loading_parameters.flat_after = ImageParameters(input_path=flat_after_directory, format=image_format,
                                                        prefix=get_prefix(flat_after_image), log_file=flat_after_log)

        # Dark before
        dark_before_image = find_images(Path(sample_directory), "Dark", suffix="Before", look_without_suffix=True,
                                        image_format=image_format, logger=logger)[0]
        loading_parameters.dark_after = ImageParameters(input_path=Path(sample_directory),
                                                        prefix=get_prefix(dark_before_image),
                                                        format=image_format)

        # Dark after
        dark_after_image = find_images(Path(sample_directory), "Dark", suffix="After", image_format=image_format,
                                       logger=logger)[0]
        loading_parameters.dark_after = ImageParameters(input_path=Path(sample_directory),
                                                        prefix=get_prefix(dark_after_image),
                                                        format=image_format)

        # 180 Degree projection
        lp.proj_180deg = ImageParameters(input_path=self.view.proj_180deg.directory(),
                                         prefix=os.path.splitext(self.view.proj_180deg.path_text())[0],
                                         format=self.image_format)