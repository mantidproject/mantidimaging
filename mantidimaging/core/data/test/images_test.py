import unittest

import numpy as np
from six import StringIO

from mantidimaging.core.data import Images
from mantidimaging.core.operation_history import const
from mantidimaging.test_helpers.unit_test_helper import generate_images


class ImagesTest(unittest.TestCase):
    def test_parse_metadata_file(self):
        json_file = StringIO('{"a_int": 42, "a_string": "yes", "a_arr": ["one", "two", '
                             '"three"], "a_float": 3.65e-05, "a_bool": true}')

        imgs = Images(np.asarray([1]))
        imgs.load_metadata(json_file)

        def validate_prop(k, v):
            self.assertEqual(imgs.metadata[k], v)

        validate_prop('a_bool', True)
        validate_prop('a_string', 'yes')
        validate_prop('a_int', 42)
        validate_prop('a_arr', ['one', 'two', 'three'])

    def test_record_parameters_in_metadata(self):
        imgs = Images(np.asarray([1]))
        self.assertFalse(imgs.has_history)

        imgs.record_operation('test_func',
                              'A pretty name',
                              56,
                              9002,
                              np.ndarray((800, 1024, 1024)),
                              'yes',
                              False,
                              this=765,
                              that=495.0,
                              roi=(1, 2, 3, 4))

        self.assertTrue(imgs.has_history)

        expected = {
            'operation_history': [{
                'name': 'test_func',
                'display_name': 'A pretty name',
                'args': [56, 9002, None, 'yes', False],
                'kwargs': {
                    'this': 765,
                    'that': 495.0,
                    'roi': (1, 2, 3, 4)
                },
            }]
        }

        self.assertIn(const.TIMESTAMP, imgs.metadata[const.OPERATION_HISTORY][0])

        imgs.metadata[const.OPERATION_HISTORY][0].pop(const.TIMESTAMP)
        self.assertEqual(imgs.metadata, expected)

    def test_free_memory(self):
        images = generate_images(automatic_free=False)
        self.assertIsNotNone(images.memory_filename)
        self.assertIsNotNone(images.data)
        images.free_memory()
        self.assertIsNone(images.memory_filename)
        self.assertIsNone(images.data)
