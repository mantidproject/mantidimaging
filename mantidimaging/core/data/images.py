import datetime
import json
import pprint
from copy import deepcopy
from typing import List, Tuple, Optional, Any, Dict

import numpy as np

from mantidimaging.core.operation_history import const
from mantidimaging.core.parallel import utility as pu
from mantidimaging.core.utility.sensible_roi import SensibleROI


class Images:
    NO_FILENAME_IMAGE_TITLE_STRING = "Image: {}"

    def __init__(self, data: np.ndarray, filenames: Optional[List[str]] = None,
                 indices: Optional[Tuple[int, int, int]] = None, metadata: Optional[Dict[str, Any]] = None,
                 sinograms: bool = False, memory_filename: Optional[str] = None):
        """

        :param data: Images of the Sample/Projection data
        :param filenames: All filenames that were matched for loading
        :param indices: Indices that were actually loaded
        :param metadata: Properties to copy when creating a new stack from an existing one
        """

        self._data = data
        self.indices = indices

        self._filenames = filenames

        self.metadata: Dict[str, Any] = deepcopy(metadata) if metadata else {}
        self._is_sinograms = sinograms

        self.memory_filename = memory_filename
        self._proj_180deg: Optional[np.ndarray] = None

    def __str__(self):
        return f'Image Stack: data={self.data.shape} | properties|={len(self.metadata)}'

    def count(self) -> int:
        return len(self._filenames) if self._filenames else 0

    def free_memory(self, delete_filename=True):
        """
        Delete the memory file containing the data, and the references to it within this class.

        The memory will not be freed until _all_ references to it are gone, so local variables
        can safely keep a reference even after deletion. This is used in unit testing data
        generation, and ROI normalisation.

        :param delete_filename: Whether to reset the memory filename attribute.
                                Set this to False in cases where the data will be replaced with
                                data with a new shape (rebin, crop), but the memory filename
                                ought to remain the same.
        """
        if self.memory_filename is not None:
            pu.delete_shared_array(self.memory_filename)
            if delete_filename:
                self.memory_filename = None
        self.data = None

    @property
    def filenames(self) -> Optional[List[str]]:
        return self._filenames

    @filenames.setter
    def filenames(self, new_ones: List[str]):
        assert len(new_ones) == self.data.shape[0], "Number of filenames and number of images must match."
        self._filenames = new_ones

    @property
    def has_history(self) -> bool:
        return const.OPERATION_HISTORY in self.metadata

    @property
    def metadata_pretty(self):
        pp = pprint.PrettyPrinter(indent=2)
        return pp.pformat(self.metadata)

    def load_metadata(self, f):
        self.metadata = json.load(f)
        self._is_sinograms = self.metadata.get(const.SINOGRAMS, False)

    def save_metadata(self, f):
        self.metadata[const.SINOGRAMS] = self.is_sinograms
        json.dump(self.metadata, f)

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
            const.TIMESTAMP: datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            const.OPERATION_NAME: func_name,
            const.OPERATION_ARGS: [a if accepted_type(a) else None for a in args],
            const.OPERATION_KEYWORD_ARGS: {k: prepare(v) for k, v in kwargs.items() if accepted_type(v)},
            const.OPERATION_DISPLAY_NAME:
                display_name
        })

    def copy(self, flip_axes=False) -> 'Images':
        shape = (self.data.shape[1], self.data.shape[0], self.data.shape[2]) if flip_axes else self.data.shape
        data_name = pu.create_shared_name()
        data_copy = pu.create_array(shape, self.data.dtype, data_name)
        if flip_axes:
            data_copy[:] = np.swapaxes(self.data, 0, 1)
        else:
            data_copy[:] = self.data[:]

        images = Images(data_copy, indices=deepcopy(self.indices), metadata=deepcopy(self.metadata),
                        sinograms=not self.is_sinograms if flip_axes else self.is_sinograms,
                        memory_filename=data_name)
        return images

    def index_as_images(self, index) -> 'Images':
        return Images(np.asarray([self.data[index]]), metadata=deepcopy(self.metadata),
                      sinograms=self.is_sinograms)

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

    def proj180deg(self):
        if self._proj_180deg is not None:
            return self._proj_180deg
        else:
            # best guess when the real 180 degree projection is lacking
            # it's likely the middle of the stack is not _exactly_ 180 degrees
            # so the calculated COR will be a few pixels off
            return self.projection(self.num_projections // 2)

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
    def dtype(self):
        return self._data.dtype

    @staticmethod
    def create_shared_images(shape, dtype, metadata):
        shared_name = pu.create_shared_name()
        arr = pu.create_array(shape, dtype, shared_name)
        return Images(arr, memory_filename=shared_name, metadata=metadata)

    @property
    def is_sinograms(self):
        return self._is_sinograms
