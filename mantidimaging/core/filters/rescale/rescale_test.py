import numpy
import pytest
from numpy import testing as npt

import mantidimaging.test_helpers.unit_test_helper as th
from mantidimaging.core.filters.rescale import RescaleFilter
from mantidimaging.test_helpers.qt_mocks import MockQSpinBox, MockQComboBox


@pytest.mark.parametrize('value', [255.0, 65535.0, 2147483647.0])
def test_rescale(value):
    images = th.generate_images((10, 100, 100))

    images.data[0:3] = -100.0
    images.data[3:6] = 0.5
    images.data[6:10] = 1.0

    images = RescaleFilter.filter_func(images, 0.0, value)
    numpy.isin(-100.0, images.data)

    npt.assert_equal(images.data[3:6], value / 2)
    npt.assert_equal(images.data[6:10], value)


def test_execute_wrapper_no_preset():
    min_output = MockQSpinBox(42.0)
    max_output = MockQSpinBox(420.0)
    preset = MockQComboBox('None')
    partial = RescaleFilter.execute_wrapper(min_output, max_output, preset)
    assert partial.keywords['min_output'] == 42.0
    assert partial.keywords['max_output'] == 420.0


@pytest.mark.parametrize(
    'type, expected_max',
    [
        ('int8', 255.0),
        ('int16', 65535),
        ('int32', 2147483647.0),
    ]
)
def test_execute_wrapper_with_preset(type: str, expected_max: float):
    min_output = MockQSpinBox(34.0)
    max_output = MockQSpinBox(420.0)
    preset = MockQComboBox(type)
    partial = RescaleFilter.execute_wrapper(min_output, max_output, preset)

    assert partial.keywords['min_output'] == 0.0
    assert partial.keywords['max_output'] == expected_max
