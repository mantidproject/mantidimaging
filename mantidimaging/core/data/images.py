import json
import pprint
from typing import List, Tuple, Optional, Any, Dict

import numpy as np

from mantidimaging import helper as h
from . import const


class Images:
    NO_FILENAME_IMAGE_TITLE_STRING = "Image: {}"

    def __init__(self, sample, flat=None, dark=None,
                 sample_filenames: Optional[List[str]] = None,
                 indices: Optional[Tuple[int, int, int]] = None,
                 flat_filenames: Optional[List[str]] = None,
                 dark_filenames: Optional[List[str]] = None,
                 properties: Optional[Dict[str, Any]] = None):
        """

        :param sample: Images of the Sample/Projection data
        :param flat: Images of the Flat data
        :param dark: Images of the Dark data
        :param sample_filenames: All filenames that were matched for loading
        :param indices: Indices that were actually loaded
        :param flat_filenames: All filenames that were matched for loading of Flat images
        :param dark_filenames: All filenames that were matched for loading of Dark images
        :param properties: Properties to copy when creating a new stack from an existing one
        """

        self.sample = sample
        self.flat = flat
        self.dark = dark
        self.indices = indices

        self._filenames = sample_filenames
        self._flat_filenames = flat_filenames
        self._dark_filenames = dark_filenames

        self.properties: Dict[str, Any] = properties if properties else {}

    def __str__(self):
        return 'Image Stack: sample={}, flat={}, dark={}, |properties|={}'.format(
            self.sample.shape if self.sample is not None else None,
            self.flat.shape if self.flat is not None else None,
            self.dark.shape if self.dark is not None else None,
            len(self.properties))

    def count(self) -> int:
        return len(self._filenames) if self._filenames else 0

    @property
    def filenames(self) -> Optional[List[str]]:
        return self._filenames

    def image_title(self, index: int) -> str:
        """
        Return the correct filename for the index. This uses the sample filenames

        It uses the step in the indices to determine which file
        from the list of all files is the one relevant to the provided index.

        :param index: Index that will be mapped to the list of all filenames, using the loading step,
                      to give the correct filename
        :return:
        """
        if self._filenames and self.indices:
            return self._filenames[index * self.indices[2]]
        else:
            return self.NO_FILENAME_IMAGE_TITLE_STRING.format(index)

    @property
    def has_history(self) -> bool:
        return const.OPERATION_HISTORY in self.properties

    @property
    def properties_pretty(self):
        pp = pprint.PrettyPrinter(indent=2)
        return pp.pformat(self.properties)

    def metadata_load(self, f):
        self.properties = json.load(f)

    def metadata_loads(self, s):
        self.properties = json.loads(s)

    def metadata_save(self, f):
        json.dump(self.properties, f)

    def metadata_saves(self):
        return json.dumps(self.properties)

    def record_parameters_in_metadata(self, func, *args, **kwargs):
        if const.OPERATION_HISTORY not in self.properties:
            self.properties[const.OPERATION_HISTORY] = []

        def accepted_type(o):
            return type(o) in [str, int, float, bool, tuple, list]

        self.properties[const.OPERATION_HISTORY].append({
            const.OPERATION_NAME: func,
            const.OPERATION_ARGS:
                [a if accepted_type(a) else None for a in args],
            const.OPERATION_KEYWORD_ARGS:
                dict([(k, v if accepted_type(v) else None) for (k, v)
                      in kwargs.items()])
        })

    @staticmethod
    def check_data_stack(data, expected_dims=3, expected_class=np.ndarray):
        h.check_data_stack(data, expected_dims, expected_class)
