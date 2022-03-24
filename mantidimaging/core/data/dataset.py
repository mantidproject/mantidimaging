# Copyright (C) 2022 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
import uuid
from dataclasses import dataclass
from typing import Optional, List

import numpy as np

from mantidimaging.core.data import ImageStack
from mantidimaging.core.data.reconlist import ReconList


def _delete_stack_error_message(images_id: uuid.UUID) -> str:
    return f"Unable to delete stack: ImageStack with ID {images_id} not present in dataset."


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

    def replace(self, images_id: uuid.UUID, new_data: np.ndarray):
        for image in self.all:
            if image.id == images_id:
                image.data = new_data
                return
        raise KeyError(f"Unable to replace: ImageStack with ID {images_id} not present in dataset.")

    def __contains__(self, images_id: uuid.UUID) -> bool:
        return any([image.id == images_id for image in self.all])

    @property
    def all_image_ids(self) -> List[uuid.UUID]:
        return [image_stack.id for image_stack in self.all if image_stack is not None]

    def delete_recons(self):
        self.recons.clear()


class MixedDataset(BaseDataset):
    def __init__(self, stacks: List[ImageStack] = [], name: str = ""):
        super().__init__(name=name)
        self._stacks = stacks

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
    def nexus_arrays(self) -> List[np.ndarray]:
        image_stacks = [self.dark_before, self.flat_before, self.sample, self.flat_after, self.dark_after]
        return [images.data for images in image_stacks if images is not None]

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
