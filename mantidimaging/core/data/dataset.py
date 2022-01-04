# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
import uuid
from dataclasses import dataclass
from typing import Optional, List

import numpy as np

from mantidimaging.core.data import Images


def _delete_stack_error_message(images_id: uuid.UUID) -> str:
    return f"Unable to delete stack: Images with ID {images_id} not present in dataset."


class BaseDataset:
    def __init__(self):
        self._id: uuid.UUID = uuid.uuid4()
        self.recons: List[Images] = []

    @property
    def id(self) -> uuid.UUID:
        return self._id

    @property
    def all(self):
        return NotImplementedError()

    def delete_stack(self, images_id: uuid.UUID):
        return NotImplementedError()

    def replace(self, images_id: uuid.UUID, new_data: np.ndarray):
        for image in self.all:
            if image.id == images_id:
                image.data = new_data
                return
        raise KeyError(f"Unable to replace: Images with ID {images_id} not present in dataset.")

    def __contains__(self, images_id: uuid.UUID) -> bool:
        return any([image.id == images_id for image in self.all])

    @property
    def all_image_ids(self) -> List[uuid.UUID]:
        return [image_stack.id for image_stack in self.all if image_stack is not None]


class StackDataset(BaseDataset):
    def __init__(self, stacks: List[Images] = []):
        super(StackDataset, self).__init__()
        self._stacks = stacks

    @property
    def all(self) -> List[Images]:
        return self._stacks + self.recons

    def delete_stack(self, images_id: uuid.UUID):
        for image in self.all:
            if image.id == images_id:
                self._stacks.remove(image)
                return
        raise KeyError(_delete_stack_error_message(images_id))


@dataclass
class Dataset(BaseDataset):
    sample: Images
    flat_before: Optional[Images] = None
    flat_after: Optional[Images] = None
    dark_before: Optional[Images] = None
    dark_after: Optional[Images] = None

    def __init__(self,
                 sample: Images,
                 flat_before: Optional[Images] = None,
                 flat_after: Optional[Images] = None,
                 dark_before: Optional[Images] = None,
                 dark_after: Optional[Images] = None):
        super(Dataset, self).__init__()
        self.sample = sample
        self.flat_before = flat_before
        self.flat_after = flat_after
        self.dark_before = dark_before
        self.dark_after = dark_after

    @property
    def all(self) -> List[Images]:
        image_stacks = [
            self.sample, self.sample.proj180deg, self.flat_before, self.flat_after, self.dark_before, self.dark_after
        ]
        return [image_stack for image_stack in image_stacks if image_stack is not None] + self.recons

    def delete_stack(self, images_id: uuid.UUID):
        if isinstance(self.sample, Images) and self.sample.id == images_id:
            self.sample = None  # type: ignore
        elif isinstance(self.flat_before, Images) and self.flat_before.id == images_id:
            self.flat_before = None
        elif isinstance(self.flat_after, Images) and self.flat_after.id == images_id:
            self.flat_after = None
        elif isinstance(self.dark_before, Images) and self.dark_before.id == images_id:
            self.dark_before = None
        elif isinstance(self.dark_after, Images) and self.dark_after.id == images_id:
            self.dark_after = None
        elif images_id in [recon.id for recon in self.recons]:
            for recon in self.recons:
                if recon.id == images_id:
                    self.recons.remove(recon)
        else:
            raise KeyError(_delete_stack_error_message(images_id))
