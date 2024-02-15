# Copyright (C) 2024 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

import numpy as np
from unittest import mock

import pytest
import numpy.testing as npt

from mantidimaging.test_helpers import unit_test_helper as th
from mantidimaging.core.parallel.utility import _create_shared_array, execute_impl, multiprocessing_necessary,\
    copy_into_shared_memory


@pytest.mark.parametrize(
    'shape,is_shared_data,should_be_parallel',
    (
        [11, False, False],  # not shared data should return False
        # shapes <= 10 should return False
        [10, True, False],
        # shapes > 10 with shared data should return True
        [11, True, True]))
def test_correctly_chooses_parallel(shape: int, is_shared_data: bool, should_be_parallel: bool):
    assert multiprocessing_necessary(shape, is_shared_data) is should_be_parallel


def test_execute_impl_seq():
    mock_partial = mock.Mock()
    mock_progress = mock.Mock()
    execute_impl(1, mock_partial, False, mock_progress, "Test")
    mock_partial.assert_called_once_with(0)
    mock_progress.update.assert_called_once_with(1, "Test")


@mock.patch('mantidimaging.core.parallel.utility.pm.pool')
def test_execute_impl_par(mock_pool):
    mock_partial = mock.Mock()
    mock_progress = mock.Mock()
    mock_pool.imap.return_value = range(15)
    execute_impl(15, mock_partial, True, mock_progress, "Test")
    mock_pool.imap.assert_called_once()
    assert mock_progress.update.call_count == 15


@pytest.mark.parametrize('dtype,expected_dtype', [
    [np.uint8, np.uint8],
    ['uint8', np.uint8],
    [np.uint16, np.uint16],
    ['uint16', np.uint16],
    [np.int32, np.int32],
    ['int32', np.int32],
    [np.int64, np.int64],
    ['int64', np.int64],
    [np.float32, np.float32],
    ['float32', np.float32],
    [np.float64, np.float64],
    ['float64', np.float64],
])
def test_create_shared_array(dtype, expected_dtype):
    arr = _create_shared_array((10, 10, 10), dtype)
    assert arr.array.dtype == expected_dtype
    assert arr._free_mem_on_del


def test_copy_into_shared_memory():
    array = np.zeros((5, 5, 5), np.float32)
    shared_array = copy_into_shared_memory(array)
    assert shared_array.has_shared_memory
    assert shared_array._free_mem_on_del
    npt.assert_equal(shared_array.array, array)


def test_looking_up_shared_array_from_proxy():
    shape = (5, 5, 5)
    dtype = np.float32
    array = th.gen_img_numpy_rand(shape)

    # Create an array in shared memory to look up
    shared_array = _create_shared_array(shape, dtype)
    shared_array.array[:] = array[:]

    # Create the proxy
    proxy = shared_array.array_proxy
    assert proxy._shared_array is None

    # Call the array property of the proxy to look up the shared array
    npt.assert_equal(shared_array.array, proxy.array)
    assert proxy._shared_array
    assert not proxy._shared_array._free_mem_on_del
    assert shared_array._shared_memory.name == proxy._shared_array._shared_memory.name


if __name__ == "__main__":
    import pytest

    pytest.main([__file__])
