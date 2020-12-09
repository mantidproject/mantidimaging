# Copyright (C) 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later

import mock
import numpy as np

from mantidimaging.core.parallel.utility import create_array, free_all_owned_by_this_instance, multiprocessing_necessary, execute_impl
import SharedArray as sa


def test_correctly_chooses_parallel():
    # forcing 1 core should always return False
    assert multiprocessing_necessary((100, 10, 10), cores=1) is False
    # shapes less than 10 should return false
    assert multiprocessing_necessary((10, 10, 10), cores=12) is False
    assert multiprocessing_necessary(10, cores=12) is False
    # shapes over 10 should return True
    assert multiprocessing_necessary((11, 10, 10), cores=12) is True
    assert multiprocessing_necessary(11, cores=12) is True


@mock.patch('mantidimaging.core.parallel.utility.Pool')
def test_execute_impl_one_core(mock_pool):
    mock_partial = mock.Mock()
    mock_progress = mock.Mock()
    execute_impl(1, mock_partial, 1, 1, mock_progress, "Test")
    mock_partial.assert_called_once_with(0)
    mock_progress.update.assert_called_once_with(1, "Test")


@mock.patch('mantidimaging.core.parallel.utility.Pool')
def test_execute_impl_par(mock_pool):
    mock_partial = mock.Mock()
    mock_progress = mock.Mock()
    mock_pool_instance = mock.Mock()
    mock_pool_instance.imap.return_value = range(15)
    mock_pool.return_value.__enter__.return_value = mock_pool_instance
    execute_impl(15, mock_partial, 10, 1, mock_progress, "Test")
    mock_pool_instance.imap.assert_called_once()
    assert mock_progress.update.call_count == 15


def test_free_all_owned_by_this_instance():
    [sa.delete(x.name.decode("utf-8")) for x in sa.list()]
    create_array((10, 10), np.float32, random_name=True)
    create_array((10, 10), np.float32, random_name=True)
    create_array((10, 10), np.float32, random_name=True)

    temp_name = "not_this_instance"
    sa.create("not_this_instance", (10, 10))

    assert len(sa.list()) == 4
    free_all_owned_by_this_instance()
    assert len(sa.list()) == 1
    sa.delete(temp_name)


if __name__ == "__main__":
    import pytest

    pytest.main([__file__])
