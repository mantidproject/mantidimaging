from __future__ import absolute_import, division, print_function

import unittest

from six import StringIO
import numpy as np

from mantidimaging.core.data import Images


class ImagesTest(unittest.TestCase):

    def test_to_string_empty(self):
        imgs = Images()
        self.assertEquals(
                str(imgs),
                'Image Stack: sample=None, flat=None, dark=None, '
                '|properties|=0')

    def test_to_string_with_sample(self):
        sample = np.ndarray(shape=(2, 64, 64))
        imgs = Images(sample)
        self.assertEquals(
                str(imgs),
                'Image Stack: sample=(2, 64, 64), flat=None, dark=None, '
                '|properties|=0')

    def test_serialise_metadata(self):
        imgs = Images()
        imgs.properties['a_bool'] = True
        imgs.properties['a_string'] = 'yes'
        imgs.properties['a_float'] = 3.65e-5
        imgs.properties['a_int'] = 42
        imgs.properties['a_arr'] = ['one', 'two', 'three']

        def validate_str(s):
            for k in imgs.properties.keys():
                self.assertTrue(k in s)

        s = imgs.metadata_saves()
        validate_str(s)

        f = StringIO()
        imgs.metadata_save(f)
        validate_str(f.getvalue())

    def test_parse_metadata_file(self):
        json_file = StringIO(
                '{"a_int": 42, "a_string": "yes", "a_arr": ["one", "two", '
                '"three"], "a_float": 3.65e-05, "a_bool": true}')

        imgs = Images()
        imgs.metadata_load(json_file)

        def validate_prop(k, v):
            self.assertEquals(imgs.properties[k], v)

        validate_prop('a_bool', True)
        validate_prop('a_string', 'yes')
        validate_prop('a_int', 42)
        validate_prop('a_arr', ['one', 'two', 'three'])

    def test_parse_metadata_str(self):
        json_str = \
                '{"a_int": 42, "a_string": "yes", "a_arr": ["one", "two", ' \
                '"three"], "a_float": 3.65e-05, "a_bool": true}'

        imgs = Images()
        imgs.metadata_loads(json_str)

        def validate_prop(k, v):
            self.assertEquals(imgs.properties[k], v)

        validate_prop('a_bool', True)
        validate_prop('a_string', 'yes')
        validate_prop('a_int', 42)
        validate_prop('a_arr', ['one', 'two', 'three'])
