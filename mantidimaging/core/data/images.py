import json
import pprint
from copy import deepcopy
from typing import List, Tuple, Optional, Any, Dict

import numpy as np

from mantidimaging import helper as h
from mantidimaging.core.operation_history import const


class Images:
    NO_FILENAME_IMAGE_TITLE_STRING = "Image: {}"

    def __init__(self,
                 sample: np.ndarray,
                 flat: np.ndarray = None,
                 dark: np.ndarray = None,
                 sample_filenames: Optional[List[str]] = None,
                 indices: Optional[Tuple[int, int, int]] = None,
                 flat_filenames: Optional[List[str]] = None,
                 dark_filenames: Optional[List[str]] = None,
                 metadata: Optional[Dict[str, Any]] = None):
        """

        :param sample: Images of the Sample/Projection data
        :param flat: Images of the Flat data
        :param dark: Images of the Dark data
        :param sample_filenames: All filenames that were matched for loading
        :param indices: Indices that were actually loaded
        :param flat_filenames: All filenames that were matched for loading of Flat images
        :param dark_filenames: All filenames that were matched for loading of Dark images
        :param metadata: Properties to copy when creating a new stack from an existing one
        """

        self.sample = sample
        self.flat = flat
        self.dark = dark
        self.indices = indices

        self._filenames = sample_filenames
        self._flat_filenames = flat_filenames
        self._dark_filenames = dark_filenames

        self.metadata: Dict[str, Any] = deepcopy(metadata) if metadata else {}

    def __str__(self):
        return 'Image Stack: sample={}, flat={}, dark={}, |properties|={}'.format(
            self.sample.shape if self.sample is not None else None, self.flat.shape if self.flat is not None else None,
            self.dark.shape if self.dark is not None else None, len(self.metadata))

    def count(self) -> int:
        return len(self._filenames) if self._filenames else 0

    @property
    def filenames(self) -> Optional[List[str]]:
        return self._filenames

    @filenames.setter
    def filenames(self, new_ones: List[str]):
        assert len(new_ones) == self.sample.shape[0], "Number of filenames and number of images must match."
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

    def save_metadata(self, f):
        json.dump(self.metadata, f)

    def record_operation(self, func_name: str, display_name=None, *args, **kwargs):
        if const.OPERATION_HISTORY not in self.metadata:
            self.metadata[const.OPERATION_HISTORY] = []

        def accepted_type(o):
            return type(o) in [str, int, float, bool, tuple, list]

        self.metadata[const.OPERATION_HISTORY].append({
            const.OPERATION_NAME:
                func_name,
            const.OPERATION_ARGS: [a if accepted_type(a) else None for a in args],
            const.OPERATION_KEYWORD_ARGS: {k: v
                                           for k, v in kwargs.items() if accepted_type(v)},
            const.OPERATION_DISPLAY_NAME:
                display_name
        })

    @staticmethod
    def check_data_stack(data, expected_dims=3, expected_class=np.ndarray):
        h.check_data_stack(data, expected_dims, expected_class)
