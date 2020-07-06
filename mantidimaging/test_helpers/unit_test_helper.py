import os
import sys
from typing import Tuple

import numpy as np
import numpy.testing as npt
from six import StringIO

from mantidimaging.core.data import Images
from mantidimaging.core.parallel import utility as pu

backup_mp_avail = None
g_shape = (10, 8, 10)


def gen_img_numpy_rand(shape=g_shape) -> np.ndarray:
    return np.random.rand(*shape)


def generate_shared_array_and_copy(shape=g_shape) -> Tuple[np.ndarray, np.ndarray]:
    arr = generate_shared_array(shape)
    copy = np.copy(arr)
    return arr, copy


def generate_shared_array(shape=g_shape, dtype=np.float32) -> np.ndarray:
    with pu.temp_shared_array(shape, dtype) as generated_array:
        np.copyto(generated_array, np.random.rand(shape[0], shape[1], shape[2]).astype(dtype))
        return generated_array


def generate_images(shape=g_shape, dtype=np.float32, automatic_free=True) -> Images:
    import inspect
    import uuid
    array_name = f"{str(uuid.uuid4())}{inspect.stack()[1].function}"
    if automatic_free:
        with pu.temp_shared_array(shape, dtype, force_name=array_name) as d:
            return _set_random_data(d, shape, array_name)
    else:
        d = pu.create_array(shape, dtype, array_name)
        return _set_random_data(d, shape, array_name)


def _set_random_data(data, shape, array_name):
    n = np.random.rand(*shape)
    # move the data in the shared array
    data[:] = n[:]

    images = Images(data)
    images.memory_filename = array_name
    return images


def gen_empty_shared_array(shape=g_shape):
    with pu.temp_shared_array(shape) as d:
        return d


def gen_img_shared_array_with_val(val=1., shape=g_shape):
    with pu.temp_shared_array(shape) as d:
        n = np.full(shape, val)
        # move the data in the shared array
        d[:] = n[:]
        return d


def assert_not_equals(one: np.ndarray, two: np.ndarray):
    """
    Assert equality for numpy ndarrays using the numpy testing library.

    :param one: The left side of the comparison

    :param two: The right side of the comparison
    """
    assert isinstance(one, np.ndarray)
    assert isinstance(two, np.ndarray)
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


def switch_mp_off():
    """
    This function does very bad things that should never be replicated.
    But it's a unit test so it's fine.
    """
    # backup function so we can restore it
    global backup_mp_avail
    backup_mp_avail = pu.multiprocessing_available

    def simple_return_false():
        return False

    # do bad things, swap out the function to one that returns false
    pu.multiprocessing_available = simple_return_false


def switch_mp_on():
    """
    This function does very bad things that should never be replicated.
    But it's a unit test so it's fine.
    """
    # restore the original backed up function from switch_mp_off
    pu.multiprocessing_available = backup_mp_avail


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
            cls.assertTrue(os.path.isfile(f))

    else:
        filename = base_name + file_extension_separator + file_extension
        cls.assertTrue(os.path.isfile(filename))


class IgnoreOutputStreams(object):
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


def shared_deepcopy(images: Images) -> np.ndarray:
    with pu.temp_shared_array(images.data.shape) as copy:
        np.copyto(copy, images.data)
        return copy
