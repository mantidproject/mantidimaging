# Copyright (C) 2022 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
import uuid
from logging import getLogger
from typing import Dict, Optional, List, Union, NoReturn, TYPE_CHECKING

from mantidimaging.core.data import ImageStack
from mantidimaging.core.data.dataset import StrictDataset, MixedDataset
from mantidimaging.core.io import loader, saver
from mantidimaging.core.utility.data_containers import LoadingParameters, ProjectionAngles

if TYPE_CHECKING:
    from mantidimaging.core.utility.progress_reporting import Progress

logger = getLogger(__name__)


def _matching_dataset_attribute(dataset_attribute: Optional[ImageStack], images_id: uuid.UUID) -> bool:
    return isinstance(dataset_attribute, ImageStack) and dataset_attribute.id == images_id


class MainWindowModel(object):
    def __init__(self):
        super().__init__()
        self.datasets: Dict[uuid.UUID, Union[MixedDataset, StrictDataset]] = {}

    def get_images_by_uuid(self, images_uuid: uuid.UUID) -> Optional[ImageStack]:
        for dataset in self.datasets.values():
            for image in dataset.all:
                if images_uuid == image.id:
                    return image
        return None

    def do_load_dataset(self, parameters: LoadingParameters, progress) -> StrictDataset:
        sample = loader.load_p(parameters.sample, parameters.dtype, progress)
        ds = StrictDataset(sample)

        sample._is_sinograms = parameters.sinograms
        sample.pixel_size = parameters.pixel_size

        if parameters.sample.log_file:
            ds.sample.log_file = loader.load_log(parameters.sample.log_file)

        if parameters.flat_before:
            flat_before = loader.load_p(parameters.flat_before, parameters.dtype, progress)
            ds.flat_before = flat_before
            if parameters.flat_before.log_file:
                flat_before.log_file = loader.load_log(parameters.flat_before.log_file)
        if parameters.flat_after:
            flat_after = loader.load_p(parameters.flat_after, parameters.dtype, progress)
            ds.flat_after = flat_after
            if parameters.flat_after.log_file:
                flat_after.log_file = loader.load_log(parameters.flat_after.log_file)

        if parameters.dark_before:
            dark_before = loader.load_p(parameters.dark_before, parameters.dtype, progress)
            ds.dark_before = dark_before
        if parameters.dark_after:
            dark_after = loader.load_p(parameters.dark_after, parameters.dtype, progress)
            ds.dark_after = dark_after

        if parameters.proj_180deg:
            sample.proj180deg = loader.load_p(parameters.proj_180deg, parameters.dtype, progress)

        self.datasets[ds.id] = ds
        return ds

    def load_images_into_mixed_dataset(self, file_path: str, progress: 'Progress') -> MixedDataset:
        images = self.load_image_stack(file_path, progress)
        sd = MixedDataset([images], images.name)
        self.datasets[sd.id] = sd
        return sd

    @staticmethod
    def load_image_stack(file_path: str, progress: 'Progress') -> ImageStack:
        return loader.load_stack(file_path, progress)

    def do_images_saving(self, images_id, output_dir, name_prefix, image_format, overwrite, pixel_depth, progress):
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
        return True

    def do_nexus_saving(self, dataset_id: uuid.UUID, path: str, sample_name: str) -> Optional[bool]:
        if dataset_id in self.datasets and isinstance(self.datasets[dataset_id], StrictDataset):
            saver.nexus_save(self.datasets[dataset_id], path, sample_name)  # type: ignore
            return True
        else:
            raise RuntimeError(f"Failed to get StrictDataset with ID {dataset_id}")

    def get_existing_180_id(self, dataset_id: uuid.UUID) -> Optional[uuid.UUID]:
        """
        Gets the ID of the 180 projection object in a Dataset.
        :param dataset_id: The Dataset ID.
        :return: The 180 ID if found, None otherwise.
        """
        if dataset_id in self.datasets and isinstance(self.datasets[dataset_id], StrictDataset):
            dataset = self.datasets[dataset_id]
        else:
            raise RuntimeError(f"Failed to get StrictDataset with ID {dataset_id}")

        if isinstance(dataset.proj180deg, ImageStack):  # type: ignore
            return dataset.proj180deg.id  # type: ignore
        return None

    def add_180_deg_to_dataset(self, dataset_id: uuid.UUID, _180_deg_file: str) -> ImageStack:
        """
        Loads the 180 projection and adds this to a given Dataset ID.
        :param dataset_id: The ID of the Dataset.
        :param _180_deg_file: The location of the 180 projection.
        :return: The loaded 180 ImageStack object.
        """
        if dataset_id in self.datasets:
            dataset = self.datasets[dataset_id]
        else:
            raise RuntimeError(f"Failed to get Dataset with ID {dataset_id}")

        if not isinstance(dataset, StrictDataset):
            raise RuntimeError(f"Wrong dataset type passed to add 180 method: {dataset_id}")

        _180_deg = loader.load(file_names=[_180_deg_file])
        dataset.proj180deg = _180_deg
        return _180_deg

    def add_projection_angles_to_sample(self, images_id: uuid.UUID, proj_angles: ProjectionAngles):
        images = self.get_images_by_uuid(images_id)
        if images is None:
            self.raise_error_when_images_not_found(images_id)
        images.set_projection_angles(proj_angles)

    def raise_error_when_images_not_found(self, images_id: uuid.UUID) -> NoReturn:
        raise RuntimeError(f"Failed to get ImageStack with ID {images_id}")

    def raise_error_when_parent_dataset_not_found(self, images_id: uuid.UUID) -> NoReturn:
        raise RuntimeError(f"Failed to find dataset containing ImageStack with ID {images_id}")

    def raise_error_when_parent_strict_dataset_not_found(self, images_id: uuid.UUID) -> NoReturn:
        raise RuntimeError(f"Failed to find strict dataset containing ImageStack with ID {images_id}")

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
        del self.datasets[dataset_id]

    def remove_container(self, container_id: uuid.UUID) -> List[uuid.UUID]:
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
                    # If we're deleting a sample from a StrictDataset then any linked 180 projection will also be
                    # deleted
                    if isinstance(dataset, StrictDataset) and dataset.proj180deg and dataset.sample.id == container_id:
                        proj_180_id = dataset.proj180deg.id
                    dataset.delete_stack(container_id)
                    return [container_id, proj_180_id] if proj_180_id else [container_id]
                if container_id == dataset.recons.id:
                    ids_to_remove = dataset.recons.ids
                    dataset.delete_recons()
                    return ids_to_remove
        self.raise_error_when_images_not_found(container_id)

    def add_dataset_to_model(self, dataset: Union[StrictDataset, MixedDataset]) -> None:
        self.datasets[dataset.id] = dataset

    @property
    def image_ids(self) -> List[uuid.UUID]:
        images = []
        for dataset in self.datasets.values():
            images += dataset.all
        return [image.id for image in images if image is not None]

    @property
    def images(self) -> List[ImageStack]:
        images = []
        for dataset in self.datasets.values():
            images += dataset.all
        return images

    @property
    def proj180s(self) -> List[ImageStack]:
        proj180s = []
        for dataset in self.datasets.values():
            if isinstance(dataset, StrictDataset) and dataset.proj180deg is not None:
                proj180s.append(dataset.proj180deg)
        return proj180s

    def get_parent_dataset(self, member_id: uuid.UUID) -> uuid.UUID:
        """
        Takes the ID of an image stack and returns the ID of its parent strict dataset.
        :param member_id: The ID of the image stack.
        :return: The ID of the parent dataset if found.
        """
        for dataset in self.datasets.values():
            if member_id in dataset:
                return dataset.id
        self.raise_error_when_parent_dataset_not_found(member_id)

    def add_recon_to_dataset(self, recon_data: ImageStack, stack_id: uuid.UUID) -> uuid.UUID:
        """
        Adds a recon to a dataset using recon data and an ID from one of the stacks in the dataset.
        :param recon_data: The recon data.
        :param stack_id: The ID of one of the member stacks.
        :return: The ID of the parent dataset if found.
        """
        for dataset in self.datasets.values():
            if stack_id in dataset:
                dataset.recons.append(recon_data)
                return dataset.id
        self.raise_error_when_parent_strict_dataset_not_found(stack_id)

    @property
    def recon_list_ids(self):
        return [dataset.recons.id for dataset in self.datasets.values()]

    def get_recon_list_id(self, parent_id: uuid.UUID) -> uuid.UUID:
        return self.datasets[parent_id].recons.id
