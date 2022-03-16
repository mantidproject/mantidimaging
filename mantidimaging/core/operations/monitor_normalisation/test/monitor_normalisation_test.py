# Copyright (C) 2022 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from functools import partial

from unittest import mock
import numpy as np
import numpy.testing as npt

from mantidimaging.core.utility.data_containers import Counts
from mantidimaging.test_helpers.unit_test_helper import generate_images, assert_not_equals
from ..monitor_normalisation import MonitorNormalisation
from mantidimaging.test_helpers.start_qapplication import start_shared_memory_manager, shutdown_shared_memory_manager


def test_one_projection():
    start_shared_memory_manager()
    images = generate_images((1, 1, 1))
    images._log_file = mock.Mock()
    images._log_file.counts = mock.Mock(return_value=Counts(np.sin(np.linspace(0, 1, images.num_projections))))
    npt.assert_raises(RuntimeError, MonitorNormalisation.filter_func, images)
    shutdown_shared_memory_manager()


def test_no_counts():
    start_shared_memory_manager()
    images = generate_images((2, 2, 2))
    images._log_file = mock.Mock()
    images._log_file.counts = mock.Mock(return_value=None)
    npt.assert_raises(RuntimeError, MonitorNormalisation.filter_func, images)
    shutdown_shared_memory_manager()


def test_execute():
    start_shared_memory_manager()
    images = generate_images()
    images._log_file = mock.Mock()
    images._log_file.counts = mock.Mock(return_value=Counts(np.sin(np.linspace(0, 1, images.num_projections))))

    original = images.copy()
    MonitorNormalisation.filter_func(images)
    images._log_file.counts.assert_called_once()
    assert_not_equals(original.data, images.data)
    shutdown_shared_memory_manager()


def test_execute2():
    """
    Test that the counts are correctly divided by the value at counts[0].

    In this test that will make all the counts equal to 1, and the data will remain unchanged
    """
    start_shared_memory_manager()
    images = generate_images()
    images._log_file = mock.Mock()
    images._log_file.counts = mock.Mock(return_value=Counts(np.full((10, ), 10)))

    original = images.copy()
    MonitorNormalisation.filter_func(images)
    images._log_file.counts.assert_called_once()
    npt.assert_equal(original.data, images.data)
    shutdown_shared_memory_manager()


def test_register_gui():
    assert MonitorNormalisation.register_gui(None, None, None) == {}


def test_execute_wrapper():
    wrapper = MonitorNormalisation.execute_wrapper()
    assert wrapper is not None
    assert isinstance(wrapper, partial)


def test_validate_execute_kwargs():
    assert MonitorNormalisation.validate_execute_kwargs({}) is True
