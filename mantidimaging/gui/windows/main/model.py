# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
import os
import uuid
from collections import namedtuple
from logging import getLogger
from typing import Dict, List

from mantidimaging.core.data import Images
from mantidimaging.core.data.dataset import Dataset
from mantidimaging.core.io import loader, saver
from mantidimaging.core.utility.data_containers import LoadingParameters, ProjectionAngles
from mantidimaging.gui.windows.stack_visualiser import StackVisualiserView

logger = getLogger(__name__)


class MainWindowModel(object):
    def __init__(self):
        super(MainWindowModel, self).__init__()

        self.datasets: List[Dataset] = []
        self.images: Dict[uuid.UUID, Images] = {}
        self._stack_names = {}

    def do_load_dataset(self, parameters: LoadingParameters, progress):
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

        self.datasets[ds.uu_id] = ds
        return ds

    def load_images(self, file_path: str, progress) -> Images:
        images = loader.load_stack(file_path, progress)
        self.images[images.uu_id] = images.uu_id
        return images

    def do_images_saving(self, stack_uuid, output_dir, name_prefix, image_format, overwrite, pixel_depth, progress):
        images = self.get_images_by_uuid(stack_uuid)
        filenames = saver.save(images,
                               output_dir=output_dir,
                               name_prefix=name_prefix,
                               overwrite_all=overwrite,
                               out_format=image_format,
                               pixel_depth=pixel_depth,
                               progress=progress)
        images.filenames = filenames
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

    def update_images(self, images_uuid: uuid.UUID, new_images: Images):
        """
        Updates the images of an existing dataset/images object.
        :param images_uuid: The id of the image to update.
        :param new_images: The new images data.
        """
        for _, dataset in self.datasets:
            if dataset.sample.uu_id == images_uuid:
                dataset.sample = new_images
                return
            if isinstance(dataset.flat_before, Dataset) and dataset.flat_before.uu_id == images_uuid:
                dataset.flat_before = new_images
                return
            if isinstance(dataset.flat_after, Dataset) and dataset.flat_after.uu_id == images_uuid:
                dataset.flat_after = new_images
                return
            if isinstance(dataset.dark_before, Dataset) and dataset.dark_before.uu_id == images_uuid:
                dataset.dark_before = new_images
                return
            if isinstance(dataset.dark_after, Dataset) and dataset.dark_after.uu_id == images_uuid:
                dataset.dark_after = new_images
                return

        for id, images in self.images:
            if id == images_uuid:
                images = new_images
                return
        # todo: what happens if you get here?

        # if not stack.presenter.images == images:
        #     stack.image_view.clear()
        #     stack.image_view.setImage(images.data)
        #
        #     # Free previous images stack before reassignment
        #     stack.presenter.images = images

    def add_180_deg_to_dataset(self, stack_name, _180_deg_file):
        stack_dock = self.get_stack_by_name(stack_name)
        if stack_dock is None:
            raise RuntimeError(f"Failed to get stack with name {stack_name}")

        _180_deg = loader.load(file_names=[_180_deg_file]).sample
        stack_dock.presenter.images.proj180deg = _180_deg
        return _180_deg

    def add_projection_angles_to_sample(self, stack_name: str, proj_angles: ProjectionAngles):
        stack_dock = self.get_stack_by_name(stack_name)
        if stack_dock is None:
            raise RuntimeError(f"Failed to get stack with name {stack_name}")

        stack: StackVisualiserView = stack_dock.widget()  # type: ignore
        images: Images = stack.presenter.images
        images.set_projection_angles(proj_angles)

    def get_images_by_uuid(self, images_uuid: uuid.UUID):
        for _, dataset in self.datasets:
            if dataset.sample.uu_id == images_uuid:
                return dataset.sample
            if isinstance(dataset.flat_before, Dataset) and dataset.flat_before.uu_id == images_uuid:
                return dataset.flat_before
            if isinstance(dataset.flat_after, Dataset) and dataset.flat_after.uu_id == images_uuid:
                return dataset.flat_after
            if isinstance(dataset.dark_before, Dataset) and dataset.dark_before.uu_id == images_uuid:
                return dataset.dark_before
            if isinstance(dataset.dark_after, Dataset) and dataset.dark_after.uu_id == images_uuid:
                return dataset.dark_after
        for id, images in self.images:
            if id == images_uuid:
                return images
        # todo: what happens if you get here?

    def load_log(self, log_file: str):
        return loader.load_log(log_file)
