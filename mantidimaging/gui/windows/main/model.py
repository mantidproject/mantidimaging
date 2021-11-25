# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
import uuid
from logging import getLogger
from typing import Dict, Optional, List

import numpy as np

from mantidimaging.core.data import Images
from mantidimaging.core.data.dataset import Dataset
from mantidimaging.core.data.loadingdataset import LoadingDataset
from mantidimaging.core.io import loader, saver
from mantidimaging.core.utility.data_containers import LoadingParameters, ProjectionAngles

logger = getLogger(__name__)


def _matching_dataset_attribute(dataset_attribute: Optional[Images], images_id: uuid.UUID) -> bool:
    return isinstance(dataset_attribute, Images) and dataset_attribute.id == images_id


class MainWindowModel(object):
    def __init__(self):
        super(MainWindowModel, self).__init__()

        self.datasets: Dict[uuid.UUID, Dataset] = {}
        self.images: Dict[uuid.UUID, Images] = {}

    def get_images_by_uuid(self, images_uuid: uuid.UUID):
        if images_uuid in self.images:
            return self.images[images_uuid]
        return None

    def do_load_dataset(self, parameters: LoadingParameters, progress) -> Dataset:
        sample = loader.load_p(parameters.sample, parameters.dtype, progress)
        self.images[sample.id] = sample
        ds = Dataset(sample)

        sample._is_sinograms = parameters.sinograms
        sample.pixel_size = parameters.pixel_size

        if parameters.sample.log_file:
            ds.sample.log_file = loader.load_log(parameters.sample.log_file)

        if parameters.flat_before:
            flat_before = loader.load_p(parameters.flat_before, parameters.dtype, progress)
            self.images[flat_before.id] = flat_before
            ds.flat_before = flat_before
            if parameters.flat_before.log_file:
                flat_before.log_file = loader.load_log(parameters.flat_before.log_file)
        if parameters.flat_after:
            flat_after = loader.load_p(parameters.flat_after, parameters.dtype, progress)
            self.images[flat_after.id] = flat_after
            ds.flat_after = flat_after
            if parameters.flat_after.log_file:
                flat_after.log_file = loader.load_log(parameters.flat_after.log_file)

        if parameters.dark_before:
            dark_before = loader.load_p(parameters.dark_before, parameters.dtype, progress)
            self.images[dark_before.id] = dark_before
            ds.dark_before = dark_before
        if parameters.dark_after:
            dark_after = loader.load_p(parameters.dark_after, parameters.dtype, progress)
            self.images[dark_after.id] = dark_after
            ds.dark_after = dark_after

        if parameters.proj_180deg:
            sample.proj180deg = loader.load_p(parameters.proj_180deg, parameters.dtype, progress)

        self.datasets[ds.id] = ds
        return ds

    def convert_loading_dataset(self, loading_dataset: LoadingDataset) -> Dataset:
        self.images[loading_dataset.sample.id] = loading_dataset.sample
        ds = Dataset(loading_dataset.sample)

        if isinstance(loading_dataset.flat_before, Images):
            self.images[loading_dataset.flat_before.id] = ds.flat_before = loading_dataset.flat_before
        if isinstance(loading_dataset.flat_after, Images):
            self.images[loading_dataset.flat_after.id] = ds.flat_after = loading_dataset.flat_after

        if isinstance(loading_dataset.dark_before, Images):
            self.images[loading_dataset.dark_before.id] = ds.dark_before = loading_dataset.dark_before
        if isinstance(loading_dataset.dark_after, Images):
            self.images[loading_dataset.dark_after.id] = ds.dark_after = loading_dataset.dark_after

        self.datasets[ds.id] = ds
        return ds

    def load_images(self, file_path: str, progress) -> Images:
        images = loader.load_stack(file_path, progress)
        self.images[images.id] = images
        return images

    def do_images_saving(self, images_id, output_dir, name_prefix, image_format, overwrite, pixel_depth, progress):
        images = self.get_images_by_uuid(images_id)
        if images is None:
            self.raise_error_when_images_not_found(images_id)
        filenames = saver.save(images,
                               output_dir=output_dir,
                               name_prefix=name_prefix,
                               overwrite_all=overwrite,
                               out_format=image_format,
                               pixel_depth=pixel_depth,
                               progress=progress)
        images.filenames = filenames
        return True

    def set_image_data_by_uuid(self, images_id: uuid.UUID, new_data: np.ndarray):
        """
        Updates the data of an existing dataset/images object.
        :param images_id: The id of the image to update.
        :param new_data: The new image data.
        """
        if images_id in self.images:
            self.images[images_id].data = new_data
        else:
            self.raise_error_when_images_not_found(images_id)

    def add_180_deg_to_dataset(self, images_id: uuid.UUID, _180_deg_file: str) -> Images:
        """
        Loads to 180 projection and adds this to a given Images ID.
        :param images_id: The ID of the Images object.
        :param _180_deg_file: The location of the 180 projection.
        :return: The loaded 180 Image object.
        """
        images = self.get_images_by_uuid(images_id)
        if images is None:
            self.raise_error_when_images_not_found(images_id)
        _180_deg = loader.load(file_names=[_180_deg_file]).sample
        images.proj180deg = _180_deg
        return _180_deg

    def add_projection_angles_to_sample(self, images_id: uuid.UUID, proj_angles: ProjectionAngles):
        images = self.get_images_by_uuid(images_id)
        if images is None:
            self.raise_error_when_images_not_found(images_id)
        images.set_projection_angles(proj_angles)

    def raise_error_when_images_not_found(self, images_id: uuid.UUID):
        raise RuntimeError(f"Failed to get Images with ID {images_id}")

    def add_log_to_sample(self, images_id: uuid.UUID, log_file: str):
        images = self.get_images_by_uuid(images_id)
        if images is None:
            raise RuntimeError
        log = loader.load_log(log_file)
        log.raise_if_angle_missing(images.filenames)
        images.log_file = log

    def _remove_dataset(self, dataset_id: uuid.UUID):
        """
        Removes a dataset and the image stacks it contains from the model.
        :param dataset_id: The dataset ID.
        """
        dataset = self.datasets[dataset_id]
        del self.images[dataset.sample.id]

        if isinstance(dataset.flat_before, Images):
            del self.images[dataset.flat_before.id]
        if isinstance(dataset.flat_after, Images):
            del self.images[dataset.flat_after.id]
        if isinstance(dataset.dark_before, Images):
            del self.images[dataset.dark_before.id]
        if isinstance(dataset.dark_after, Images):
            del self.images[dataset.dark_after.id]

        del self.datasets[dataset_id]

    def remove_container(self, container_id: uuid.UUID) -> Optional[List[uuid.UUID]]:
        """
        Removes a container from the model.
        :param container_id: The ID of the dataset or image stack.
        :return: A list of the IDs of all the image stacks that were deleted from the model if a match was found, None
            otherwise.
        """
        if container_id in self.images:
            del self.images[container_id]
            return [container_id]
        if container_id in self.datasets:
            stacks_in_dataset = self.datasets[container_id].all_image_ids
            self._remove_dataset(container_id)
            return stacks_in_dataset
        self.raise_error_when_images_not_found(container_id)
        return None
