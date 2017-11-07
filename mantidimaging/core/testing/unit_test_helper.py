from __future__ import absolute_import, division, print_function

import os
import sys

from six import StringIO

import numpy as np
import numpy.testing as npt

from mantidimaging.core.parallel import utility as pu

backup_mp_avail = None
g_shape = (10, 8, 10)


def gen_img_numpy_rand(shape=g_shape):
    return np.random.rand(*shape)


def gen_img_shared_array_and_copy(shape=g_shape):
    arr = gen_img_shared_array(shape)
    copy = shared_deepcopy(arr)
    return arr, copy


def gen_img_shared_array(shape=g_shape):
    d = pu.create_shared_array(shape)
    n = np.random.rand(shape[0], shape[1], shape[2])
    # move the data in the shared array
    d[:] = n[:]

    return d


def generate_images_class_random_shared_array(shape=g_shape):
    from mantidimaging.core.data import Images
    d = pu.create_shared_array(shape)
    n = np.random.rand(shape[0], shape[1], shape[2])
    # move the data in the shared array
    d[:] = n[:]

    images = Images(d)

    return images


def gen_empty_shared_array(shape=g_shape):
    d = pu.create_shared_array(shape)
    return d


def gen_img_shared_array_with_val(val=1., shape=g_shape):
    d = pu.create_shared_array(shape)
    n = np.full(shape, val)
    # move the data in the shared array
    d[:] = n[:]

    return d


def assert_not_equals(numpy_ndarray1, numpy_ndarray2):
    """
    Assert equality for numpy ndarrays using the numpy testing library.

    :param numpy_ndarray1: The left side of the comparison

    :param numpy_ndarray2: The right side of the comparison
    """
    npt.assert_raises(AssertionError,
                      npt.assert_equal,
                      numpy_ndarray1, numpy_ndarray2)


def deepcopy(source):
    from copy import deepcopy
    return deepcopy(source)


def shared_deepcopy(source):
    d = pu.create_shared_array(source.shape)
    from copy import deepcopy
    d[:] = deepcopy(source)[:]
    return d


def debug(switch=True):
    if switch:
        import pydevd
        pydevd.settrace(
            'localhost', port=59003, stdoutToServer=True, stderrToServer=True)


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


def assert_files_exist(cls, base_name, file_extension,
                       file_extension_separator='.', single_file=True,
                       num_images=1):
    """
    Asserts that the
    :param cls: Must be a unittest.TestCase class, in order to use the
                assertTrue
    :param base_name: The base name of the filename.
    :param file_extension: The expected extension
    :param file_extension_separator: The extension separator. It should
                                     normally always be '.'
    :param single_file: Are we looking for a 'stack' of images
    """
    import unittest
    assert isinstance(
        cls, unittest.TestCase
    ), "Work only if class is unittest.TestCase, it uses self.assertTrue!"

    if not single_file:
        # generate a list of filenames with 000000 numbers appended
        filenames = []
        for i in range(num_images):
            filenames.append(base_name + str(i) +
                             file_extension_separator + file_extension)

        for f in filenames:
            cls.assertTrue(os.path.isfile(f))

    else:
        filename = base_name + file_extension_separator + file_extension
        cls.assertTrue(os.path.isfile(filename))


def mock_property(obj, object_property, property_return_value=None):
    """
    Mock a property of the object. This is a helper function to work around the
    limitations of mocking a property with different return values.

    :param obj: The object whose property will be mocked.

    :param object_property: The property that will be mocked as a string.

    :param property_return_value: The expected return value

    :returns: The PropertyMock object that you can do assertions with
    """
    import mantidimaging.core.utility.special_imports as imps
    mock = imps.import_mock()
    temp_property_mock = mock.PropertyMock(return_value=property_return_value)
    setattr(type(obj), object_property, temp_property_mock)
    return temp_property_mock


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
