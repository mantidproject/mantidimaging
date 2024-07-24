# Copyright (C) 2024 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations
import uuid
from dataclasses import dataclass

import numpy as np

from mantidimaging.core.data import ImageStack
from mantidimaging.core.data.reconlist import ReconList
from mantidimaging.core.utility.data_containers import FILE_TYPES


def _delete_stack_error_message(images_id: uuid.UUID) -> str:
    return f"Unable to delete stack: ImageStack with ID {images_id} not present in dataset."


def _image_key_list(key: int, n_images: int) -> list[int]:
    return [key for _ in range(n_images)]


def remove_nones(image_stacks: list[ImageStack | None]) -> list[ImageStack]:
    return [image_stack for image_stack in image_stacks if image_stack is not None]


class BaseDataset:

    def __init__(self, *, name: str = "", stacks: list[ImageStack] | None = None) -> None:
        self._id: uuid.UUID = uuid.uuid4()
        self.name = name

        self._recons = ReconList()
        self._sinograms: ImageStack | None = None
        stacks = [] if stacks is None else stacks
        self._stacks: list[ImageStack] = stacks

    @property
    def id(self) -> uuid.UUID:
        return self._id

    @property
    def sinograms(self) -> ImageStack | None:
        return self._sinograms

    @sinograms.setter
    def sinograms(self, sino: ImageStack | None) -> None:
        self._sinograms = sino

    @property
    def all(self) -> list[ImageStack]:
        return self.recons.stacks + self._stacks + remove_nones([self._sinograms])

    def delete_stack(self, images_id: uuid.UUID) -> None:
        for recon in self.recons:
            if recon.id == images_id:
                self.recons.remove(recon)
                return
        for image in self._stacks:
            if image.id == images_id:
                self._stacks.remove(image)
                return
        if self.sinograms is not None and self.sinograms.id == images_id:
            self.sinograms = None
            return
        raise KeyError(_delete_stack_error_message(images_id))

    def __contains__(self, images_id: uuid.UUID) -> bool:
        return any(image.id == images_id for image in self.all)

    @property
    def all_image_ids(self) -> list[uuid.UUID]:
        return [image_stack.id for image_stack in self.all if image_stack is not None]

    @property
    def recons(self) -> ReconList:
        return self._recons

    def add_recon(self, recon: ImageStack) -> None:
        self.recons.append(recon)

    def delete_recons(self) -> None:
        self.recons.clear()

    def add_stack(self, stack: ImageStack) -> None:
        self._stacks.append(stack)


class MixedDataset(BaseDataset):
    pass


@dataclass
class StrictDataset(BaseDataset):
    sample: ImageStack
    flat_before: ImageStack | None = None
    flat_after: ImageStack | None = None
    dark_before: ImageStack | None = None
    dark_after: ImageStack | None = None

    def __init__(self,
                 sample: ImageStack,
                 flat_before: ImageStack | None = None,
                 flat_after: ImageStack | None = None,
                 dark_before: ImageStack | None = None,
                 dark_after: ImageStack | None = None,
                 name: str = ""):
        super().__init__(name=name)
        self.sample = sample
        self.flat_before = flat_before
        self.flat_after = flat_after
        self.dark_before = dark_before
        self.dark_after = dark_after

        if self.name == "":
            self.name = sample.name

    @property
    def all(self) -> list[ImageStack]:
        image_stacks = [
            self.sample, self.proj180deg, self.flat_before, self.flat_after, self.dark_before, self.dark_after,
            self.sinograms
        ]
        return remove_nones(image_stacks) + self.recons.stacks

    @property
    def _nexus_stack_order(self) -> list[ImageStack]:
        return list(filter(None, [self.dark_before, self.flat_before, self.sample, self.flat_after, self.dark_after]))

    @property
    def nexus_arrays(self) -> list[np.ndarray]:
        return [image_stack.data for image_stack in self._nexus_stack_order]

    @property
    def nexus_rotation_angles(self) -> list[np.ndarray]:
        proj_angles = []
        for image_stack in self._nexus_stack_order:
            angles = image_stack.real_projection_angles()
            proj_angles.append(angles.value if angles else np.zeros(image_stack.num_images))
        return proj_angles

    @property
    def image_keys(self) -> list[int]:
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
    def proj180deg(self) -> ImageStack | None:
        if self.sample is not None:
            return self.sample.proj180deg
        else:
            return None

    @proj180deg.setter
    def proj180deg(self, proj180deg: ImageStack | None) -> None:
        self.sample.proj180deg = proj180deg

    def delete_stack(self, images_id: uuid.UUID) -> None:
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

    def set_stack(self, file_type: FILE_TYPES, image_stack: ImageStack) -> None:
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


def _get_stack_data_type(stack_id: uuid.UUID, dataset: BaseDataset) -> str:
    """
    Find the data type as a string of a stack.
    :param stack_id: The ID of the stack.
    :param dataset: The parent dataset of the stack.
    :return: A string of the stack's data type.
    """
    if stack_id in [recon.id for recon in dataset.recons]:
        return "Recon"
    if stack_id in [stack.id for stack in dataset._stacks]:
        return "Images"
    if isinstance(dataset, StrictDataset):
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
