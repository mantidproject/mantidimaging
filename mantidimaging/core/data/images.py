import json
import pprint

import numpy as np

from . import const
from mantidimaging import helper as h


class Images(object):
    def __init__(self, sample=None, flat=None, dark=None, filenames=None):

        self._sample = sample
        self._flat = flat
        self._dark = dark

        self._filenames = filenames

        self.properties = {}

    def __str__(self):
        return \
            'Image Stack: sample={}, flat={}, dark={}, |properties|={}'.format(
                self.sample.shape if self.sample is not None else None,
                self.flat.shape if self.flat is not None else None,
                self.dark.shape if self.dark is not None else None,
                len(self.properties))

    @property
    def sample(self):
        return self._sample

    @sample.setter
    def sample(self, imgs):
        self._sample = imgs

    @property
    def flat(self):
        return self._flat

    @flat.setter
    def flat(self, imgs):
        self._flat = imgs

    @property
    def dark(self):
        return self._dark

    @dark.setter
    def dark(self, imgs):
        self._dark = imgs

    @property
    def filenames(self):
        return self._filenames

    @property
    def has_history(self):
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
