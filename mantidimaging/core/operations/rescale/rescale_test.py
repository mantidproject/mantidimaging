import pytest
from numpy import testing as npt, int16, float32, finfo, copy

import mantidimaging.test_helpers.unit_test_helper as th
from mantidimaging.core.operations.rescale import RescaleFilter
from mantidimaging.test_helpers.qt_mocks import MockQSpinBox, MockQComboBox


@pytest.mark.parametrize('value', [255.0, 65535.0, 2147483647.0])
def test_rescale(value):
    images = th.generate_images((10, 100, 100))

    images.data[0:3] = -100.0
    images.data[3:6] = 0.5
    images.data[6:10] = 1.0

    expected_min_input = 0.1
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


@pytest.mark.parametrize('type, max_value', [(int16, 65535), (float32, finfo(float32).max)])
def test_type_changes_to_given_type(type, max_value):
    images = th.generate_images((10, 100, 100))

    expected_min_input = 0
    images = RescaleFilter.filter_func(images,
                                       min_input=expected_min_input,
                                       max_input=images.data.max(),
                                       max_output=max_value,
                                       data_type=type)

    npt.assert_equal(images.dtype, type)


def test_scale_single_image():
    images = th.generate_images((2, 100, 100))

    images.data[0] = -100.0
    images.data[1] = 1.5

    # Scale to int16
    scaled_image1 = RescaleFilter.filter_single_image(copy(images.data[0]), 0, images.data.max(),
                                                      1, data_type=int16)
    scaled_image2 = RescaleFilter.filter_single_image(copy(images.data[1]), 0, images.data.max(),
                                                      1, data_type=int16)

    npt.assert_equal(0, scaled_image1)
    npt.assert_equal(1, scaled_image2)

    # Scale to float32
    scaled_image3 = RescaleFilter.filter_single_image(copy(images.data[0]), 0, images.data.max(),
                                                      2, data_type=float32)
    scaled_image4 = RescaleFilter.filter_single_image(copy(images.data[1]), 0, images.data.max(),
                                                      2, data_type=float32)

    npt.assert_equal(0.0, scaled_image3)
    npt.assert_equal(2.0, scaled_image4)

    assert scaled_image1.dtype == int16
    assert scaled_image2.dtype == int16
    assert scaled_image3.dtype == float32
    assert scaled_image4.dtype == float32


if __name__ == "__main__":
    import pytest

    pytest.main([__file__])
