# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
import uuid
from logging import getLogger
from typing import Dict, Optional

from mantidimaging.core.data import Images
from mantidimaging.core.data.dataset import Dataset
from mantidimaging.core.io import loader, saver
from mantidimaging.core.utility.data_containers import LoadingParameters, ProjectionAngles

logger = getLogger(__name__)


def _matching_dataset_attribute(dataset_attribute: Optional[Images], images_id: uuid.UUID) -> bool:
    return isinstance(dataset_attribute, Images) and dataset_attribute.id == images_id


def load_log(log_file: str):
    return loader.load_log(log_file)


class MainWindowModel(object):
    def __init__(self):
        super(MainWindowModel, self).__init__()

        self.datasets: Dict[uuid.UUID, Dataset] = {}
        self.images: Dict[uuid.UUID, Images] = {}

    def get_images_by_uuid(self, images_uuid: uuid.UUID):
        if images_uuid in self.images:
            return self.images[images_uuid]
        return None

    def do_load_dataset(self, parameters: LoadingParameters, progress):
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

    def load_images(self, file_path: str, progress) -> Images:
        images = loader.load_stack(file_path, progress)
        self.images[images.id] = images.id
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

    def set_images_by_uuid(self, images_id: uuid.UUID, new_images: Images):
        """
        Updates the images of an existing dataset/images object.
        :param images_id: The id of the image to update.
        :param new_images: The new images data.
        """
        if images_id in self.images:
            self.images[images_id] = new_images
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
        log = load_log(log_file)
        log.raise_if_angle_missing(images.filenames)
        images.log_file = log
        # todo - send update here or do it from presenter?
        
    def _remove_image_stack(self, images_id: uuid.UUID):
        del self.images[images_id]
        for dataset in self.datasets.values():
            # if _matching_dataset_attribute(dataset.sample, images_id):
            #     dataset.sample = None # todo - allow this?
            if _matching_dataset_attribute(dataset.flat_before, images_id):
                del self.images[dataset.flat_before.id]
                return
            if _matching_dataset_attribute(dataset.flat_after, images_id):
                del self.images[dataset.flat_after.id]
                return
            if _matching_dataset_attribute(dataset.dark_before, images_id):
                del self.images[dataset.dark_before.id]
                return
            if _matching_dataset_attribute(dataset.dark_after, images_id):
                del self.images[dataset.dark_after.id]
                return

    def _remove_dataset(self, dataset_id: uuid.UUID):
        dataset = self.datasets[dataset_id]
        del self.images[dataset.sample.id]
        del self.images[dataset.flat_before.id]
        del self.images[dataset.flat_after.id]
        del self.images[dataset.dark_before.id]
        del self.images[dataset.dark_after.id]
        del self.datasets[dataset_id]

    def remove_container(self, container_id: uuid.UUID):
        if container_id in self.images:
            self._remove_image_stack(container_id)
        if container_id in self.datasets:
            self._remove_dataset(container_id)
