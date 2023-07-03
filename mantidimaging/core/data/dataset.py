# Copyright (C) 2023 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations
import uuid
from dataclasses import dataclass
from typing import Optional, List, Union

import numpy as np

from mantidimaging.core.data import ImageStack
from mantidimaging.core.data.reconlist import ReconList
from mantidimaging.core.utility.data_containers import FILE_TYPES


def _delete_stack_error_message(images_id: uuid.UUID) -> str:
    return f"Unable to delete stack: ImageStack with ID {images_id} not present in dataset."


def _image_key_list(key: int, n_images: int):
    return [key for _ in range(n_images)]


class BaseDataset:

    def __init__(self, name: str = ""):
        self._id: uuid.UUID = uuid.uuid4()
        self.recons = ReconList()
        self._name = name
        self._sinograms: Optional[ImageStack] = None

    @property
    def id(self) -> uuid.UUID:
        return self._id

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, arg: str):
        self._name = arg

    @property
    def sinograms(self) -> Optional[ImageStack]:
        return self._sinograms

    @sinograms.setter
    def sinograms(self, sino: Optional[ImageStack]):
        self._sinograms = sino

    @property
    def all(self):
        raise NotImplementedError()

    def delete_stack(self, images_id: uuid.UUID):
        raise NotImplementedError()

    def __contains__(self, images_id: uuid.UUID) -> bool:
        return any(image.id == images_id for image in self.all)

    @property
    def all_image_ids(self) -> List[uuid.UUID]:
        return [image_stack.id for image_stack in self.all if image_stack is not None]

    def add_recon(self, recon: ImageStack):
        self.recons.append(recon)

    def delete_recons(self):
        self.recons.clear()


class MixedDataset(BaseDataset):

    def __init__(self, stacks: Optional[List[ImageStack]] = None, name: str = ""):
        super().__init__(name=name)
        stacks = [] if stacks is None else stacks
        self._stacks = stacks

    def add_stack(self, stack: ImageStack):
        self._stacks.append(stack)

    @property
    def all(self) -> List[ImageStack]:
        all_images = self._stacks + self.recons.stacks
        if self.sinograms is None:
            return all_images
        return all_images + [self.sinograms]

    def delete_stack(self, images_id: uuid.UUID):
        for image in self._stacks:
            if image.id == images_id:
                self._stacks.remove(image)
                return
        for recon in self.recons:
            if recon.id == images_id:
                self.recons.remove(recon)
                return
        if self.sinograms is not None and self.sinograms.id == images_id:
            self.sinograms = None
            return
        raise KeyError(_delete_stack_error_message(images_id))


@dataclass
class StrictDataset(BaseDataset):
    sample: ImageStack
    flat_before: Optional[ImageStack] = None
    flat_after: Optional[ImageStack] = None
    dark_before: Optional[ImageStack] = None
    dark_after: Optional[ImageStack] = None

    def __init__(self,
                 sample: ImageStack,
                 flat_before: Optional[ImageStack] = None,
                 flat_after: Optional[ImageStack] = None,
                 dark_before: Optional[ImageStack] = None,
                 dark_after: Optional[ImageStack] = None,
                 name: str = ""):
        super().__init__(name=name)
        self.sample = sample
        self.flat_before = flat_before
        self.flat_after = flat_after
        self.dark_before = dark_before
        self.dark_after = dark_after

        if self.name == "":
            self._name = sample.name

    @property
    def all(self) -> List[ImageStack]:
        image_stacks = [
            self.sample, self.proj180deg, self.flat_before, self.flat_after, self.dark_before, self.dark_after,
            self.sinograms
        ]
        return [image_stack for image_stack in image_stacks if image_stack is not None] + self.recons.stacks

    @property
    def _nexus_stack_order(self) -> List[ImageStack]:
        return list(filter(None, [self.dark_before, self.flat_before, self.sample, self.flat_after, self.dark_after]))

    @property
    def nexus_arrays(self) -> List[np.ndarray]:
        return [image_stack.data for image_stack in self._nexus_stack_order]

    @property
    def nexus_rotation_angles(self) -> List[np.ndarray]:
        proj_angles = []
        for image_stack in self._nexus_stack_order:
            angles = image_stack.real_projection_angles()
            proj_angles.append(angles.value if angles else np.zeros(image_stack.num_images))
        return proj_angles

    @property
    def image_keys(self) -> List[int]:
        image_keys = []
        if self.dark_before is not None:
            image_keys += _image_key_list(2, self.dark_before.data.shape[0])
        if self.flat_before is not None:
            image_keys += _image_key_list(1, self.flat_before.data.shape[0])
        if self.sample is not None:
            image_keys += _image_key_list(0, self.sample.data.shape[0])
        else:
            raise RuntimeError("Unable to create image keys object without sample.")
        if self.flat_after is not None:
            image_keys += _image_key_list(1, self.flat_after.data.shape[0])
        if self.dark_after is not None:
            image_keys += _image_key_list(2, self.dark_after.data.shape[0])
        return image_keys

    @property
    def proj180deg(self):
        if self.sample is not None:
            return self.sample.proj180deg
        else:
            return None

    @proj180deg.setter
    def proj180deg(self, _180_deg: ImageStack):
        self.sample.proj180deg = _180_deg

    def delete_stack(self, images_id: uuid.UUID):
        if isinstance(self.sample, ImageStack) and self.sample.id == images_id:
            self.sample = None  # type: ignore
        elif isinstance(self.flat_before, ImageStack) and self.flat_before.id == images_id:
            self.flat_before = None
        elif isinstance(self.flat_after, ImageStack) and self.flat_after.id == images_id:
            self.flat_after = None
        elif isinstance(self.dark_before, ImageStack) and self.dark_before.id == images_id:
            self.dark_before = None
        elif isinstance(self.dark_after, ImageStack) and self.dark_after.id == images_id:
            self.dark_after = None
        elif isinstance(self.proj180deg, ImageStack) and self.proj180deg.id == images_id:
            self.sample.clear_proj180deg()
        elif isinstance(self.sinograms, ImageStack) and self.sinograms.id == images_id:
            self.sinograms = None
        elif images_id in self.recons.ids:
            for recon in self.recons:
                if recon.id == images_id:
                    self.recons.remove(recon)
        else:
            raise KeyError(_delete_stack_error_message(images_id))

    def set_stack(self, file_type: FILE_TYPES, image_stack: ImageStack):
        attr_name = file_type.fname.lower().replace(" ", "_")
        if file_type == FILE_TYPES.PROJ_180:
            attr_name = "proj180deg"
        if hasattr(self, attr_name):
            setattr(self, attr_name, image_stack)
        else:
            raise AttributeError(f"StrictDataset does not have an attribute for {attr_name}")

    @property
    def is_processed(self) -> bool:
        """
        :return: True if any of the data has been processed, False otherwise.
        """
        for image in self.all:
            if image.is_processed:
                return True
        return False


def _get_stack_data_type(stack_id: uuid.UUID, dataset: Union[MixedDataset, StrictDataset]) -> str:
    """
    Find the data type as a string of a stack.
    :param stack_id: The ID of the stack.
    :param dataset: The parent dataset of the stack.
    :return: A string of the stack's data type.
    """
    if stack_id in [recon.id for recon in dataset.recons]:
        return "Recon"
    if isinstance(dataset, MixedDataset):
        if stack_id in dataset:
            return "Images"
    else:
        if stack_id == dataset.sample.id:
            return "Sample"
        if dataset.flat_before is not None and stack_id == dataset.flat_before.id:
            return "Flat Before"
        if dataset.flat_after is not None and stack_id == dataset.flat_after.id:
            return "Flat After"
        if dataset.dark_before is not None and stack_id == dataset.dark_before.id:
            return "Dark Before"
        if dataset.dark_after is not None and stack_id == dataset.dark_after.id:
            return "Dark After"
    raise RuntimeError(f"No stack with ID {stack_id} found in dataset {dataset.id}")
