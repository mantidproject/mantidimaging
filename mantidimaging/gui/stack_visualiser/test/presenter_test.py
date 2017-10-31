import unittest

import numpy as np
import numpy.testing as npt

from matplotlib.widgets import Slider

import mantidimaging.core.testing.unit_test_helper as th

from mantidimaging.core.utility.special_imports import import_mock

from mantidimaging.gui.algorithm_dialog import AlgorithmDialog
from mantidimaging.gui.stack_visualiser import (
        StackVisualiserPresenter, StackVisualiserView, ImageMode, Parameters)
from mantidimaging.gui.stack_visualiser import \
        Notification as PresenterNotifications

mock = import_mock()

TEST_APPLY_BEFORE_AFTER_MAGIC_NUMBER = 42
TEST_MOCK_VIEW_ROI = (1, 2, 3, 4)


class StackVisualiserPresenterTest(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(StackVisualiserPresenterTest, self).__init__(*args, **kwargs)

    @classmethod
    def setUpClass(cls):
        cls.test_data = th.generate_images_class_random_shared_array()

    def setUp(self):
        # mock the view so it has the same methods
        self.view = mock.create_autospec(StackVisualiserView)
        self.view.slider = mock.create_autospec(Slider)
        self.presenter = StackVisualiserPresenter(self.view, self.test_data, data_traversal_axis=0)

    def apply_before_mock(self, data):
        # the data here will be a ndarray, because we extract it inside the presenter
        self.assertTrue(isinstance(data, np.ndarray))
        self.apply_before_mock_variable = TEST_APPLY_BEFORE_AFTER_MAGIC_NUMBER
        return self.apply_before_mock_variable

    def apply_after_mock(self, data, result_from_before):
        # the data here will be a ndarray, because we extract it inside the presenter
        self.assertTrue(isinstance(data, np.ndarray))
        self.assertEqual(result_from_before, TEST_APPLY_BEFORE_AFTER_MAGIC_NUMBER)

    def multiply_execute_mock(self, data):
        self.assertTrue(isinstance(data, np.ndarray))
        data *= 4

    def multiply_execute_mock_with_ROI_parameter(self, data, expected_ROI):
        self.assertTrue(isinstance(data, np.ndarray))
        self.assertTrue(expected_ROI is not None)
        data *= 4

    def algorithm_dialog_has_attributes_sanity_check(self, mock_algorithm_dialog):
        error_message = "AlgorithmDialog attributes might have changed. This test needs to be updated."
        assert hasattr(mock_algorithm_dialog, 'apply_before'), error_message
        assert hasattr(mock_algorithm_dialog, 'apply_after'), error_message
        assert hasattr(mock_algorithm_dialog, 'set_execute'), error_message
        assert hasattr(mock_algorithm_dialog, 'requested_parameter_name'), error_message

    def test_apply_to_data(self):
        mock_algorithm_dialog = mock.create_autospec(AlgorithmDialog)

        self.algorithm_dialog_has_attributes_sanity_check(mock_algorithm_dialog)

        requested_parameter_name_mock = th.mock_property(mock_algorithm_dialog, "requested_parameter_name", None)

        do_before_mock = th.mock_property(mock_algorithm_dialog, "do_before", self.apply_before_mock)
        do_after_mock = th.mock_property(mock_algorithm_dialog, "do_after", self.apply_after_mock)
        mock_algorithm_dialog.execute = mock.Mock(return_value=self.multiply_execute_mock)

        self.presenter.apply_to_data(mock_algorithm_dialog)

        do_before_mock.assert_any_call()
        do_after_mock.assert_any_call()

        # we're expecting only to be read once and moved into another variable
        requested_parameter_name_mock.assert_called_once()
        mock_algorithm_dialog.execute.assert_called_once()
        self.view.show_current_image.assert_called_once()

    def test_apply_to_data_with_parameter_ROI(self):
        mock_algorithm_dialog = mock.create_autospec(AlgorithmDialog)
        self.algorithm_dialog_has_attributes_sanity_check(mock_algorithm_dialog)

        # The function returns the MOCK object that we must use to check assertions
        requested_parameter_name_mock = th.mock_property(
            mock_algorithm_dialog, "requested_parameter_name", Parameters.ROI)

        current_roi_mock = th.mock_property(self.view, "current_roi", TEST_MOCK_VIEW_ROI)

        do_before_mock = th.mock_property(mock_algorithm_dialog, "do_before", self.apply_before_mock)
        mock_algorithm_dialog.execute = mock.Mock(return_value=self.multiply_execute_mock_with_ROI_parameter)
        do_after_mock = th.mock_property(mock_algorithm_dialog, "do_after", self.apply_after_mock)

        self.presenter.apply_to_data(mock_algorithm_dialog)

        do_before_mock.assert_any_call()
        do_after_mock.assert_any_call()

        requested_parameter_name_mock.assert_called_once()
        current_roi_mock.assert_called_once()
        self.view.show_current_image.assert_called_once()

    def test_assertion_error_apply_to_data_with_wrong_class(self):
        my_mock = mock.Mock()
        self.assertRaises(AssertionError, self.presenter.apply_to_data, my_mock)

    def test_fail_apply_to_data_with_wrong_parameter(self):
        mock_algorithm_dialog = mock.create_autospec(AlgorithmDialog)
        self.algorithm_dialog_has_attributes_sanity_check(mock_algorithm_dialog)

        # The function returns the MOCK object that we must use to check assertions
        requested_parameter_name_mock = th.mock_property(
            mock_algorithm_dialog, "requested_parameter_name", "Some other parameter")

        self.assertRaises(ValueError, self.presenter.apply_to_data, mock_algorithm_dialog)
        requested_parameter_name_mock.assert_called_once()

    def test_getattr_and_clear(self):
        # empty class that inherits from object so that we can append
        # attributes to it
        class A:
            pass

        d = A()
        d.some_attr = 3
        result = self.presenter.getattr_and_clear(d, "some_attr")
        self.assertEqual(result, 3)
        self.assertTrue(d.some_attr is None)

    def test_get_image(self):
        index = 3

        test_data = self.test_data.get_sample()

        img = self.presenter.get_image(index)
        npt.assert_equal(test_data[index], img)

        self.presenter.axis = 1
        img = self.presenter.get_image(index)
        npt.assert_equal(test_data[:, index, :], img)

        self.presenter.axis = 2
        img = self.presenter.get_image(index)
        npt.assert_equal(test_data[:, :, index], img)

        # make sure we reset it to default
        self.presenter.axis = 0
        self.assertEqual(self.presenter.axis, 0)

    def test_get_empty_fullpath(self):
        result = self.presenter.get_image_filename(3)
        # we expect an empty string as we have not set the filenames
        self.assertEqual(result, "")

    def test_do_rename_view(self):
        self.presenter.notify(PresenterNotifications.RENAME_WINDOW)
        self.view.update_title_event.assert_called_once()

    def test_do_histogram(self):
        self.presenter.notify(PresenterNotifications.HISTOGRAM)
        self.view.show_histogram_of_current_image.assert_called_once()

    def test_do_new_window_histogram(self):
        self.presenter.notify(PresenterNotifications.NEW_WINDOW_HISTOGRAM)
        self.view.show_histogram_of_current_image.assert_called_once()

    def test_show_error_message_forwarded_to_view(self):
        self.presenter.show_error("test message")
        self.view.show_error_dialog.assert_called_once_with("test message")

    def test_get_image_count_on_axis(self):
        self.assertEquals(
                self.presenter.get_image_count_on_axis(),
                self.test_data.get_sample().shape[self.presenter.axis])

    def test_scroll_stack(self):
        self.view.current_index = mock.MagicMock(return_value=3)
        self.presenter.do_scroll_stack(2)
        self.view.set_index.assert_called_once_with(5)

    def test_do_scroll_up(self):
        self.view.current_index = mock.MagicMock(return_value=3)
        self.presenter.notify(PresenterNotifications.SCROLL_UP)
        self.view.set_index.assert_called_once_with(4)

    def test_do_scroll_down(self):
        self.view.current_index = mock.MagicMock(return_value=3)
        self.presenter.notify(PresenterNotifications.SCROLL_DOWN)
        self.view.set_index.assert_called_once_with(2)

    def test_summed_image_creation(self):
        test_data = self.test_data.get_sample()

        # No summed image by default
        self.assertEquals(self.presenter.image_mode, ImageMode.STACK)
        self.assertIsNone(self.presenter.summed_image)

        # Stack mode gets image from stack
        img = self.presenter.get_image(0)
        npt.assert_equal(test_data[0], img)

        # Summed image is created when first switching to summed mode
        self.presenter.image_mode = ImageMode.SUM
        self.assertEquals(self.presenter.image_mode, ImageMode.SUM)
        self.assertIsNotNone(self.presenter.summed_image)

        # Summed mode gets summed image
        img = self.presenter.get_image(0)
        npt.assert_equal(self.presenter.summed_image, img)

        # Summed image is not deleted when switching back to stack mode
        self.presenter.image_mode = ImageMode.STACK
        self.assertEquals(self.presenter.image_mode, ImageMode.STACK)
        self.assertIsNotNone(self.presenter.summed_image)

        # Stack mode gets image from stack
        img = self.presenter.get_image(0)
        npt.assert_equal(test_data[0], img)

    def test_summed_mode_disables_stack_scrolling(self):
        # Enable summed mode
        self.presenter.image_mode = ImageMode.SUM
        self.assertEquals(self.presenter.image_mode, ImageMode.SUM)

        # Ensure scroll stack events are not processed
        self.view.current_index = mock.MagicMock(return_value=3)
        self.presenter.notify(PresenterNotifications.SCROLL_UP)
        self.view.set_index.assert_not_called()


if __name__ == '__main__':
    unittest.main()
