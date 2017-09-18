import sys
import unittest

if sys.version_info >= (3, 3):
    # Use unittest.mock on Python 3.3 and above
    import unittest.mock as mock

    if sys.version_info < (3, 6):
        # If on Python 3.5 and below then need to monkey patch this function in
        # It is available as standard on Python 3.6 and above
        def assert_called_once(_mock_self):
            self = _mock_self
            if not self.call_count == 1:
                msg = ("Expected '%s' to have been called once. Called %s times." %
                        (self._mock_name or 'mock', self.call_count))
                raise AssertionError(msg)
        unittest.mock.Mock.assert_called_once = assert_called_once
else:
    # Use mock on Python < 3.3
    import mock

import numpy as np

import mantidimaging.tests.test_helper as th
from mantidimaging.gui.algorithm_dialog import AlgorithmDialog
from mantidimaging.gui.stack_visualiser.sv_available_parameters import Parameters
from mantidimaging.gui.stack_visualiser.sv_presenter import StackVisualiserPresenter
from mantidimaging.gui.stack_visualiser.sv_presenter import Notification as PresenterNotifications
# if we do not want to import the actual View and pull in Qt, we have to create an abstract view
from mantidimaging.gui.stack_visualiser.sv_view import StackVisualiserView

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

        do_before_mock.assert_called()
        do_after_mock.assert_called()

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

        do_before_mock.assert_called()
        do_after_mock.assert_called()

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
        th.assert_equals(test_data[index], img)

        self.presenter.axis = 1
        img = self.presenter.get_image(index)
        th.assert_equals(test_data[:, index, :], img)

        self.presenter.axis = 2
        img = self.presenter.get_image(index)
        th.assert_equals(test_data[:, :, index], img)

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


if __name__ == '__main__':
    unittest.main()
