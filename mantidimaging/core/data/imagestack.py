# Copyright (C) 2022 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later

import datetime
import json
import os.path
import uuid
from copy import deepcopy
from typing import List, Optional, Any, Dict, Union, TextIO, TYPE_CHECKING

import numpy as np

from mantidimaging.core.data.utility import mark_cropped
from mantidimaging.core.operation_history import const
from mantidimaging.core.parallel import utility as pu
from mantidimaging.core.utility.data_containers import ProjectionAngles, Counts, Indices
from mantidimaging.core.utility.imat_log_file_parser import IMATLogFile
from mantidimaging.core.utility.sensible_roi import SensibleROI
from mantidimaging.core.utility.leak_tracker import leak_tracker

if TYPE_CHECKING:
    from mantidimaging.core.parallel.utility import MISharedMemory


class ImageStack:
    NO_FILENAME_IMAGE_TITLE_STRING = "Image: {}"
    name: str

    def __init__(self,
                 data: Union[np.ndarray, pu.SharedArray],
                 filenames: Optional[List[str]] = None,
                 indices: Union[List[int], Indices, None] = None,
                 metadata: Optional[Dict[str, Any]] = None,
                 sinograms: bool = False,
                 name: Optional[str] = None):
        """

        :param data: a numpy array or SharedArray object containing the images of the Sample/Projection data
        :param filenames: All filenames that were matched for loading
        :param indices: Indices that were actually loaded
        :param metadata: Properties to copy when creating a new stack from an existing one
        :param name: A name for the stack
        """

        if isinstance(data, pu.SharedArray):
            self._data = data.array
            self._shared_memory: Optional['MISharedMemory'] = data.shared_memory
        else:
            self._data = data
            self._shared_memory = None

        self.indices = indices
        self._id = uuid.uuid4()

        self._filenames = filenames

        self.metadata: Dict[str, Any] = deepcopy(metadata) if metadata else {}
        self._is_sinograms = sinograms

        self._proj180deg: Optional[ImageStack] = None
        self._log_file: Optional[IMATLogFile] = None
        self._projection_angles: Optional[ProjectionAngles] = None

        if name is None:
            if filenames is not None:
                self.name = os.path.splitext(os.path.basename(filenames[0]))[0]
            else:
                self.name = "untitled"
        else:
            self.name = name

        tracker_msg = f"ImageStack {self.name}"
        leak_tracker.add(data.array if hasattr(data, 'array') else data, msg=tracker_msg)
        if hasattr(data, 'shared_memory'):
            leak_tracker.add(data.shared_memory, msg=tracker_msg)

    def __eq__(self, other):
        if isinstance(other, ImageStack):
            return np.array_equal(self.data, other.data) \
                   and self.is_sinograms == other.is_sinograms \
                   and self.metadata == other.metadata \
                   and self.indices == other.indices
        elif isinstance(other, np.ndarray):
            return np.array_equal(self.data, other)
        else:
            raise ValueError(f"Cannot compare against {other}")

    def __ne__(self, other):
        return not self == other

    def __str__(self):
        return f'Image Stack: data={self.data.shape} | properties|={len(self.metadata)}'

    def count(self) -> int:
        return len(self._filenames) if self._filenames else 0

    @property
    def filenames(self) -> Optional[List[str]]:
        return self._filenames

    @filenames.setter
    def filenames(self, new_ones: List[str]):
        assert len(new_ones) == self.data.shape[0], "Number of filenames and number of images must match."
        self._filenames = new_ones

    @property
    def id(self) -> uuid.UUID:
        return self._id

    def load_metadata(self, f: TextIO):
        self.metadata = json.load(f)
        self._is_sinograms = self.metadata.get(const.SINOGRAMS, False)

    def save_metadata(self, f: TextIO, rescale_params: Optional[Dict[str, Union[str, float]]] = None):
        self.metadata[const.SINOGRAMS] = self.is_sinograms

        if rescale_params is not None:
            self.metadata[const.RESCALED] = rescale_params

        json.dump(self.metadata, f, indent=4)

    def record_operation(self, func_name: str, display_name, *args, **kwargs):
        if const.OPERATION_HISTORY not in self.metadata:
            self.metadata[const.OPERATION_HISTORY] = []

        def accepted_type(o):
            return any([isinstance(o, expected) for expected in [str, int, float, bool, tuple, list, SensibleROI]])

        def prepare(o):
            if isinstance(o, SensibleROI):
                return list(o)
            else:
                return o

        self.metadata[const.OPERATION_HISTORY].append({
            const.TIMESTAMP:
            datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            const.OPERATION_NAME:
            func_name,
            const.OPERATION_KEYWORD_ARGS: {k: prepare(v)
                                           for k, v in kwargs.items() if accepted_type(v)},
            const.OPERATION_DISPLAY_NAME:
            display_name
        })

    def copy(self, flip_axes=False) -> 'ImageStack':
        shape = (self.data.shape[1], self.data.shape[0], self.data.shape[2]) if flip_axes else self.data.shape
        data_copy = pu.create_array(shape, self.data.dtype)
        if flip_axes:
            data_copy.array[:] = np.swapaxes(self.data, 0, 1)
        else:
            data_copy.array[:] = self.data[:]

        images = ImageStack(data_copy,
                            indices=deepcopy(self.indices),
                            metadata=deepcopy(self.metadata),
                            sinograms=not self.is_sinograms if flip_axes else self.is_sinograms)
        return images

    def copy_roi(self, roi: SensibleROI):
        shape = (self.data.shape[0], roi.height, roi.width)

        data_copy = pu.create_array(shape, self.data.dtype)
        data_copy.array[:] = self.data[:, roi.top:roi.bottom, roi.left:roi.right]

        images = ImageStack(data_copy,
                            indices=deepcopy(self.indices),
                            metadata=deepcopy(self.metadata),
                            sinograms=self._is_sinograms)

        mark_cropped(images, roi)
        return images

    def index_as_image_stack(self, index) -> 'ImageStack':
        return ImageStack(np.asarray([self.data[index]]), metadata=deepcopy(self.metadata), sinograms=self.is_sinograms)

    @property
    def height(self):
        if not self._is_sinograms:
            return self.data.shape[1]
        else:
            return self.data.shape[0]

    @property
    def width(self):
        return self.data.shape[2]

    @property
    def h_middle(self) -> float:
        """
        Returns the horizontal middle (middle column) of the projections
        """
        return self.width / 2

    @property
    def v_middle(self) -> float:
        """
        Returns the vertical middle (middle row) of the projections
        """
        return self.height / 2

    @property
    def num_images(self) -> int:
        return self.data.shape[0]

    @property
    def num_projections(self) -> int:
        if not self._is_sinograms:
            return self.data.shape[0]
        else:
            return self.data.shape[1]

    @property
    def num_sinograms(self) -> int:
        return self.height

    def sino(self, slice_idx) -> np.ndarray:
        if not self._is_sinograms:
            return np.swapaxes(self.data, 0, 1)[slice_idx]
        else:
            return self.data[slice_idx]

    def projection(self, projection_idx) -> np.ndarray:
        if self._is_sinograms:
            return np.swapaxes(self.data, 0, 1)[projection_idx]
        else:
            return self.data[projection_idx]

    def has_proj180deg(self):
        return self._proj180deg is not None

    @property
    def proj180deg(self) -> Optional['ImageStack']:
        return self._proj180deg

    @proj180deg.setter
    def proj180deg(self, value: 'ImageStack'):
        assert isinstance(value, ImageStack)
        self._proj180deg = value

    @property
    def projections(self):
        return self._data if not self._is_sinograms else np.swapaxes(self._data, 0, 1)

    @property
    def sinograms(self):
        return self._data if self._is_sinograms else np.swapaxes(self._data, 0, 1)

    @property
    def data(self) -> np.ndarray:
        return self._data

    @data.setter
    def data(self, other: np.ndarray):
        self._data = other

    @property
    def shared_memory(self) -> Optional['MISharedMemory']:
        return self._shared_memory

    @shared_memory.setter
    def shared_memory(self, memory: Optional['MISharedMemory']):
        self._shared_memory = memory

    @property
    def dtype(self):
        return self._data.dtype

    @staticmethod
    def create_empty_image_stack(shape, dtype, metadata) -> 'ImageStack':
        arr = pu.create_array(shape, dtype)
        return ImageStack(arr, metadata=metadata)

    @property
    def is_sinograms(self) -> bool:
        return self._is_sinograms

    @property
    def log_file(self):
        return self._log_file

    @log_file.setter
    def log_file(self, value: IMATLogFile):
        if value is not None:
            self.metadata[const.LOG_FILE] = value.source_file
        elif value is None:
            del self.metadata[const.LOG_FILE]
        self._log_file = value

    def set_projection_angles(self, angles: ProjectionAngles):
        if len(angles.value) != self.num_images:
            raise RuntimeError("The number of angles does not match the number of images. "
                               f"Num angles {len(angles.value)} and num images {self.num_images}")

        self._projection_angles = angles

    def projection_angles(self, max_angle: float = 360.0) -> ProjectionAngles:
        """
        Return projection angles, in priority order:
        - From a log
        - From the manually loaded file with a list of angles
        - Automatically generated with equidistant step

        :param max_angle: The maximum angle up to which the angles will be generated.
                          Only used when the angles are generated, if they are provided
                          via a log or a file the argument will be ignored.
        """
        if self._log_file is not None:
            return self._log_file.projection_angles()
        elif self._projection_angles is not None:
            return self._projection_angles
        else:
            return ProjectionAngles(np.linspace(0, np.deg2rad(max_angle), self.num_projections))

    def counts(self) -> Optional[Counts]:
        if self._log_file is not None:
            return self._log_file.counts()
        else:
            return None

    @property
    def pixel_size(self):
        return self.metadata.get(const.PIXEL_SIZE, 0)

    @pixel_size.setter
    def pixel_size(self, value: int):
        self.metadata[const.PIXEL_SIZE] = value

    def clear_proj180deg(self):
        self._proj180deg = None

    def make_name_unique(self, existing_names: List[str]):
        name = self.name
        num = 1
        while self.name in existing_names:
            num += 1
            self.name = f"{name}_{num}"

            if num > 1000:
                raise ValueError(f"Could not make unique name for: {name}")
