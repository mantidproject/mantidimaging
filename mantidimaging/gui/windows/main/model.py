# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations
import uuid
from logging import getLogger
from pathlib import Path
from typing import NoReturn, TYPE_CHECKING

from mantidimaging.core.data.dataset import Dataset
from mantidimaging.core.data.imagestack import StackNotFoundError, ImageStack
from mantidimaging.core.io import loader, saver
from mantidimaging.core.io.filenames import FilenameGroup
from mantidimaging.core.io.loader.loader import LoadingParameters, ImageParameters
from mantidimaging.core.utility.data_containers import ProjectionAngles, FILE_TYPES

if TYPE_CHECKING:
    from mantidimaging.core.utility.progress_reporting import Progress

logger = getLogger(__name__)


def _matching_dataset_attribute(dataset_attribute: ImageStack | None, images_id: uuid.UUID) -> bool:
    return isinstance(dataset_attribute, ImageStack) and dataset_attribute.id == images_id


class MainWindowModel:

    def __init__(self) -> None:
        super().__init__()
        self.datasets: dict[uuid.UUID, Dataset] = {}

    def get_images_by_uuid(self, images_uuid: uuid.UUID) -> ImageStack | None:
        for dataset in self.datasets.values():
            for image in dataset.all:
                if images_uuid == image.id:
                    return image
        return None

    # DEBUG: --------------------- THE TWO LOADING FUNCTIONS ARE HERE

    # LOADS WHOLE DATASET
    def do_load_dataset(self, parameters: LoadingParameters, progress: Progress) -> Dataset:

        def load(im_param: ImageParameters) -> ImageStack:
            return loader.load_stack_from_image_params(im_param, progress, dtype=parameters.dtype)

        sample = load(parameters.image_stacks[FILE_TYPES.SAMPLE])
        sample.create_geometry()
        ds = Dataset(sample=sample)
        sample._is_sinograms = parameters.sinograms
        sample.pixel_size = parameters.pixel_size

        for file_type in [
            FILE_TYPES.FLAT_BEFORE,
            FILE_TYPES.FLAT_AFTER,
            FILE_TYPES.DARK_BEFORE,
            FILE_TYPES.DARK_AFTER,
            FILE_TYPES.PROJ_180,
        ]:
            if im_param := parameters.image_stacks.get(file_type):
                image_stack = load(im_param)
                ds.set_stack(file_type, image_stack)

        self.datasets[ds.id] = ds
        return ds

    # DEBUG: LOADS IMAGES (SINGLE STACK AS DATASET)
    def load_image_stack_to_new_dataset(self, file_path: str, progress: Progress) -> Dataset:
        images = self.load_image_stack(file_path, progress)
        ds = Dataset(stacks=[images], name=images.name)
        self.datasets[ds.id] = ds
        return ds

    # DEBUG: ---------------------

    def load_image_stack(self, file_path: str, progress: Progress) -> ImageStack:
        group = FilenameGroup.from_file(Path(file_path))
        group.find_all_files()
        images = loader.load_stack_from_group(group, progress)
        return images

    def do_images_saving(self, images_id: uuid.UUID, output_dir: str | Path, name_prefix: str, image_format: str,
                         overwrite: bool, pixel_depth: str, progress: Progress) -> bool:
        logger.info(f"Starting export of ImageStack {images_id} to {output_dir} with format {image_format}")
        images = self.get_images_by_uuid(images_id)
        if images is None:
            self.raise_error_when_images_not_found(images_id)

        filenames = saver.image_save(images,
                                     output_dir=output_dir,
                                     name_prefix=name_prefix,
                                     overwrite_all=overwrite,
                                     out_format=image_format,
                                     pixel_depth=pixel_depth,
                                     progress=progress)

        images.filenames = filenames
        logger.info(f"Export completed. Files saved: {filenames[:2]}{' ...' if len(filenames) > 2 else ''} "
                    f"(total {len(filenames)} files)")
        return True

    def do_nexus_saving(self, dataset_id: uuid.UUID, path: Path, sample_name: str, save_as_float: bool) -> bool:
        logger.info(f"Starting NeXus export for dataset {dataset_id} to file {path}")
        dataset = self.datasets.get(dataset_id)
        if not dataset:
            raise RuntimeError(f"Failed to get Dataset with ID {dataset_id}")
        if not dataset.sample:
            raise RuntimeError(f"Dataset with ID {dataset_id} does not have a sample")
        saver.nexus_save(dataset, path, sample_name, save_as_float)
        logger.info(f"NeXus export completed successfully for dataset {dataset_id}. File saved at {path}")
        return True

    def get_existing_180_id(self, dataset_id: uuid.UUID) -> uuid.UUID | None:
        """
        Gets the ID of the 180 projection object in a Dataset.
        :param dataset_id: The Dataset ID.
        :return: The 180 ID if found, None otherwise.
        """
        dataset = self.datasets.get(dataset_id)
        if not dataset:
            raise RuntimeError(f"Failed to get Dataset with ID {dataset_id}")
        if not dataset.sample:
            raise RuntimeError(f"Dataset with ID {dataset_id} does not have a sample")

        if isinstance(dataset.proj180deg, ImageStack):
            return dataset.proj180deg.id
        return None

    def add_projection_angles_to_sample(self, images_id: uuid.UUID, proj_angles: ProjectionAngles) -> None:
        images = self.get_images_by_uuid(images_id)
        if images is None:
            self.raise_error_when_images_not_found(images_id)
        images.set_projection_angles(proj_angles)

    def raise_error_when_images_not_found(self, images_id: uuid.UUID) -> NoReturn:
        raise StackNotFoundError(f"Failed to get ImageStack with ID {images_id}")

    def raise_error_when_parent_dataset_not_found(self, images_id: uuid.UUID) -> NoReturn:
        raise StackNotFoundError(f"Failed to find dataset containing ImageStack with ID {images_id}")

    def add_log_to_sample(self, images_id: uuid.UUID, log_file: Path) -> None:
        images = self.get_images_by_uuid(images_id)
        if images is None:
            raise RuntimeError
        log = loader.load_log(log_file)
        if images.filenames is not None:
            log.raise_if_angle_missing([str(f) for f in images.filenames])
        images.log_file = log

    def add_shutter_counts_to_sample(self, images_id: uuid.UUID, shutter_counts_file: Path) -> None:
        """
        Adds the shutter counts file to the sample associated with the given images ID.
        :param images_id (uuid.UUID): The ID of the images.
        :param shutter_counts_file (Path): The path to the shutter counts file.
        :raises RuntimeError: If the images with the given ID cannot be found.
        :returns None
        """
        images = self.get_images_by_uuid(images_id)
        if images is None:
            raise RuntimeError
        images.shutter_count_file = loader.load_shutter_counts(shutter_counts_file)

    def _remove_dataset(self, dataset_id: uuid.UUID) -> None:
        """
        Removes a dataset and the image stacks it contains from the model.
        :param dataset_id: The dataset ID.
        """
        del self.datasets[dataset_id]

    def remove_container(self, container_id: uuid.UUID) -> list[uuid.UUID]:
        """
        Removes a container from the model.

        :param container_id: The ID of the dataset or image stack.
        :return: A list of the IDs of all the image stacks that were deleted from the model if a match was found, None
            otherwise.
        """
        if container_id in self.datasets:
            stacks_in_dataset = self.datasets[container_id].all_image_ids
            self._remove_dataset(container_id)
            return stacks_in_dataset
        else:
            for dataset in self.datasets.values():
                if container_id in dataset:
                    proj_180_id = None
                    # If we're deleting a sample then any linked 180 projection will also be
                    # deleted
                    if dataset.proj180deg:
                        assert dataset.sample is not None
                        if dataset.sample.id == container_id:
                            proj_180_id = dataset.proj180deg.id
                    dataset.delete_stack(container_id)
                    return [container_id, proj_180_id] if proj_180_id else [container_id]
                if container_id == dataset.recons.id:
                    ids_to_remove = dataset.recons.ids
                    dataset.delete_recons()
                    return ids_to_remove
        self.raise_error_when_images_not_found(container_id)

    def add_dataset_to_model(self, dataset: Dataset) -> None:
        self.datasets[dataset.id] = dataset

    @property
    def image_ids(self) -> list[uuid.UUID]:
        images = []
        for dataset in self.datasets.values():
            images += dataset.all
        return [image.id for image in images if image is not None]

    @property
    def images(self) -> list[ImageStack]:
        images = []
        for dataset in self.datasets.values():
            images += dataset.all
        return images

    @property
    def proj180s(self) -> list[ImageStack]:
        proj180s = []
        for dataset in self.datasets.values():
            if dataset.proj180deg is not None:
                proj180s.append(dataset.proj180deg)
        return proj180s

    def get_parent_dataset(self, member_id: uuid.UUID) -> uuid.UUID:
        """
        Takes the ID of an image stack and returns the ID of its parent dataset.
        :param member_id: The ID of the image stack.
        :return: The ID of the parent dataset if found.
        """
        for dataset in self.datasets.values():
            if member_id in dataset:
                return dataset.id
        self.raise_error_when_parent_dataset_not_found(member_id)

    @property
    def recon_list_ids(self) -> list[uuid.UUID]:
        return [dataset.recons.id for dataset in self.datasets.values()]

    def get_recon_list_id(self, parent_id: uuid.UUID) -> uuid.UUID:
        return self.datasets[parent_id].recons.id
