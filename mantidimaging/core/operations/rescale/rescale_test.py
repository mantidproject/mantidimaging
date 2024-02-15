# Copyright (C) 2024 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

import math
import numpy as np
import pytest
from numpy import testing as npt, copy

import mantidimaging.test_helpers.unit_test_helper as th
from mantidimaging.core.operations.rescale import RescaleFilter
from mantidimaging.test_helpers.qt_mocks import MockQSpinBox, MockQComboBox


@pytest.mark.parametrize('value', [255.0, 65535.0, 2147483647.0])
def test_rescale(value):
    images = th.generate_images((10, 100, 100))

    images.data[0:3] = -100
    images.data[3:6] = 0.5
    images.data[6:10] = 1.0

    expected_min_input = 0.0
    images = RescaleFilter.filter_func(images,
                                       min_input=expected_min_input,
                                       max_input=images.data.max(),
                                       max_output=value)

    # below min_input has been clipped to 0
    npt.assert_equal(0, images.data[0:3])
    npt.assert_equal(images.data[3:6], value / 2)
    npt.assert_equal(images.data[6:10], value)


def test_execute_wrapper_no_preset():
    min_input_value = 12
    max_input_value = 34

    min_input = MockQSpinBox(min_input_value)
    max_input = MockQSpinBox(max_input_value)
    max_output = MockQSpinBox(420.0)
    preset = MockQComboBox('None')
    partial = RescaleFilter.execute_wrapper(min_input, max_input, max_output, preset)
    assert partial.keywords['min_input'] == min_input_value
    assert partial.keywords['max_input'] == max_input_value
    assert partial.keywords['max_output'] == 420.0


@pytest.mark.parametrize('type, expected_max', [
    ('int8', 255.0),
    ('int16', 65535),
    ('int32', 2147483647.0),
])
def test_execute_wrapper_with_preset(type: str, expected_max: float):
    min_input_value = 12
    max_input_value = 34

    min_input = MockQSpinBox(min_input_value)
    max_input = MockQSpinBox(max_input_value)
    max_output = MockQSpinBox(420.0)  # this value is overridden by preset
    preset = MockQComboBox(type)
    partial = RescaleFilter.execute_wrapper(min_input, max_input, max_output, preset)  # type: ignore

    assert partial.keywords['min_input'] == min_input_value
    assert partial.keywords['max_input'] == max_input_value
    assert partial.keywords['max_output'] == expected_max


def test_scale_single_image():
    images = th.generate_images((2, 100, 100))

    images.data[0:2] = np.arange(-1, 1, step=0.0002).reshape(100, 100)

    scaled_image = RescaleFilter.filter_array(copy(images.data[0]),
                                              min_input=images.data[0].min(),
                                              max_input=images.data[0].max(),
                                              max_output=65535)
    assert scaled_image.min() == 0
    assert scaled_image.max() == 65535


def test_scale_single_image_bad_offset():
    images = th.generate_images((2, 100, 100))
    try:
        RescaleFilter.filter_array(copy(images.data[0]), min_input=-5000, max_input=5000, max_output=65535)
    except ValueError:
        pass
    except Exception as e:
        AssertionError(f"Unexpected exception was triggered: {e}")


@pytest.mark.parametrize('value', [255.0, 65535.0, 2147483647.0])
def test_rescale_ignores_nans(value):
    images = th.generate_images((10, 100, 100))

    images.data[0:3] = -100.0
    images.data[3:5] = 0.5
    images.data[6][0:10] = np.nan
    images.data[7:10] = 1.0

    expected_min_input = 0.0
    images = RescaleFilter.filter_func(images,
                                       min_input=expected_min_input,
                                       max_input=np.nanmax(images.data),
                                       max_output=value)

    # below min_input has been clipped to 0
    npt.assert_equal(0, images.data[0:3])

    npt.assert_equal(images.data[3:5], value / 2)
    npt.assert_equal(images.data[7:10], value)
    assert all(math.isnan(x) for x in images.data[6][0:10].flatten())


if __name__ == "__main__":
    import pytest

    pytest.main([__file__])
