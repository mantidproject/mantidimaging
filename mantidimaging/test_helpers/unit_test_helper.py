# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

import os
import sys
from functools import partial
from pathlib import Path

from unittest import mock
import numpy as np
import numpy.random
import numpy.testing as npt
from io import StringIO
import pyfakefs.fake_filesystem_unittest

from mantidimaging.core.data import ImageStack
from mantidimaging.core.data.dataset import Dataset
from mantidimaging.core.parallel import utility as pu
from mantidimaging.core.parallel.utility import SharedArray
from mantidimaging.core.utility.data_containers import ProjectionAngles

backup_mp_avail = None
g_shape = (10, 8, 10)


def gen_img_numpy_rand(shape=g_shape, seed: int | None = None) -> np.ndarray:
    if seed is not None:
        bg = np.random.PCG64(seed)
    else:
        bg = np.random.PCG64()
    rng = numpy.random.Generator(bg)
    return rng.random(shape)


def generate_images(shape=g_shape, dtype=np.float32, seed: int | None = None) -> ImageStack:
    d = pu.create_array(shape, dtype)
    return _set_random_data(d, shape, seed=seed)


def generate_images_for_parallel(shape: tuple[int, int, int] = (15, 8, 10), dtype=np.float32,
                                 seed: int | None = None) -> ImageStack:
    """
    Doesn't do anything special, just makes a number of images big enough to be
    ran in parallel from the logic of multiprocessing_necessary
    """
    d = pu.create_array(shape, dtype)
    return _set_random_data(d, shape, seed=seed)


def generate_standard_dataset(shape: tuple[int, int, int] = (2, 5, 5)) -> tuple[Dataset, list[ImageStack]]:
    image_stacks = [generate_images(shape) for _ in range(6)]
    image_stacks[0].name = "samplename"

    ds = Dataset(sample=image_stacks[0],
                 flat_before=image_stacks[1],
                 flat_after=image_stacks[2],
                 dark_before=image_stacks[3],
                 dark_after=image_stacks[4])
    ds.proj180deg = image_stacks[5]
    return ds, image_stacks


def _set_random_data(shared_array, shape, seed: int | None = None):
    n = gen_img_numpy_rand(shape, seed=seed)
    # move the data in the shared array
    shared_array.array[:] = n[:]

    images = ImageStack(shared_array)
    return images


def assert_not_equals(one: np.ndarray, two: np.ndarray):
    """
    Assert equality for numpy ndarrays using the numpy testing library.

    :param one: The left side of the comparison

    :param two: The right side of the comparison
    """
    assert isinstance(one, np.ndarray), f"LHS type isn't NDARRAY, found: {one}"
    assert isinstance(two, np.ndarray), f"RHS type isn't NDARRAY, found: {two}"
    npt.assert_raises(AssertionError, npt.assert_equal, one, two)


def deepcopy(source):
    from copy import deepcopy
    return deepcopy(source)


def debug(switch=True):
    if switch:
        import pydevd
        pydevd.settrace('localhost', port=59003, stdoutToServer=True, stderrToServer=True)


def vsdebug():
    import ptvsd
    ptvsd.enable_attach("my_secret", address=('0.0.0.0', 59003))
    print("Waiting for remote debugger at localhost:59003")
    # Enable the below line of code only if you want the application to wait
    # untill the debugger has attached to it
    ptvsd.wait_for_attach()


def assert_files_exist(cls, base_name, file_extension, file_extension_separator='.', single_file=True, num_images=1):
    """
    Asserts that a file exists.

    :param cls: Must be a unittest.TestCase class, in order to use the
                assertTrue
    :param base_name: The base name of the filename.
    :param file_extension: The expected extension
    :param file_extension_separator: The extension separator. It should
                                     normally always be '.'
    :param single_file: Are we looking for a 'stack' of images
    """
    import unittest
    assert isinstance(cls, unittest.TestCase), "Work only if class is unittest.TestCase, it uses self.assertTrue!"

    if not single_file:
        # generate a list of filenames with 000000 numbers appended
        filenames = []
        for i in range(num_images):
            filenames.append(base_name + str(i) + file_extension_separator + file_extension)

        for f in filenames:
            path = Path(f)
            cls.assertTrue(path.is_file(), f"File does not exist: {path}")
    else:
        filename = f"{base_name}{file_extension_separator}{file_extension}"
        path = Path(filename)
        cls.assertTrue(path.is_file(), f"File does not exist: {path}")


class IgnoreOutputStreams:

    def __init__(self):
        self.stdout = None
        self.stderr = None

    def __enter__(self):
        # Record the default streams
        self.stdout = sys.stdout
        self.stderr = sys.stderr

        # Replace them with string IO "dummy" buffers
        sys.stdout = StringIO()
        sys.stderr = StringIO()

    def __exit__(self, type, value, traceback):
        # Restore the default streams
        sys.stdout = self.stdout
        sys.stderr = self.stderr


def assert_called_once_with(mock: mock.Mock, *args):
    """
    Custom assert function that checks different parameter types
    with the correct assert function (i.e. numpy arrays, partials)
    """
    assert 1 == mock.call_count
    assert len(args) == len(mock.call_args[0])

    for actual, expected in zip(mock.call_args[0], args, strict=True):
        if isinstance(actual, np.ndarray):
            np.testing.assert_equal(actual, expected)
        elif isinstance(actual, ProjectionAngles):
            np.testing.assert_equal(actual.value, expected.value)
        elif isinstance(actual, ImageStack):
            assert actual is expected, f"Expected {expected}, got {actual}"
        elif isinstance(actual, partial):
            assert actual.args == expected.args
            assert actual.keywords == expected.keywords
        else:
            assert actual == expected, f"Expected {expected}, got {actual}"


class FakeFSTestCase(pyfakefs.fake_filesystem_unittest.TestCase):

    def setUp(self) -> None:
        super().setUp()
        self.setUpPyfakefs()
        if sys.platform == 'linux':
            self.fs.add_real_file("/proc/meminfo", read_only=True)

            #COMPAT: work around https://github.com/pytest-dev/pyfakefs/issues/949
            self._mock_create_shared_array = mock.patch(
                "mantidimaging.core.parallel.utility._create_shared_array",
                side_effect=lambda s, d: SharedArray(array=np.zeros(s, dtype=d), shared_memory=None))
            self._mock_create_shared_array.start()

    def tearDown(self) -> None:
        if sys.platform == 'linux':
            self._mock_create_shared_array.stop()

    def _files_equal(self, file1, file2) -> None:
        self.assertIsNotNone(file1)
        self.assertIsNotNone(file2)
        self.assertEqual(Path(file1).absolute(), Path(file2).absolute())

    def _file_list_count_equal(self, list1, list2) -> None:
        """Check that 2 lists of paths refer to the same files. Order independent"""
        self.assertCountEqual((Path(s).absolute() for s in list1), (Path(s).absolute() for s in list2))

    def _file_in_sequence(self, file1, list1) -> None:
        self.assertIn(Path(file1).absolute(), (Path(s).absolute() for s in list1))
