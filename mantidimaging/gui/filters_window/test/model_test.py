import unittest

import numpy as np

import mantidimaging.core.testing.unit_test_helper as th
from mantidimaging.core.utility.special_imports import import_mock
from mantidimaging.gui.stack_visualiser import (
        StackVisualiserView, StackVisualiserPresenter)

from mantidimaging.gui.filters_window import FiltersWindowModel

mock = import_mock()


class FiltersWindowModelTest(unittest.TestCase):

    TEST_APPLY_BEFORE_AFTER_MAGIC_NUMBER = 42

    def __init__(self, *args, **kwargs):
        super(FiltersWindowModelTest, self).__init__(*args, **kwargs)

    @classmethod
    def setUpClass(cls):
        cls.test_data = th.generate_images_class_random_shared_array()

    def setUp(self):
        self.sv_view = mock.create_autospec(StackVisualiserView)
        self.sv_presenter = StackVisualiserPresenter(
                self.sv_view, self.test_data, data_traversal_axis=0)

        self.model = FiltersWindowModel(None)

    def multiply_execute_mock(self, data):
        self.assertTrue(isinstance(data, np.ndarray))
        data *= 4
        return data

    def apply_before_mock(self, data):
        self.assertTrue(isinstance(data, np.ndarray))
        self.apply_before_mock_variable = \
            self.TEST_APPLY_BEFORE_AFTER_MAGIC_NUMBER
        return self.apply_before_mock_variable

    def apply_after_mock(self, data, result_from_before):
        self.assertTrue(isinstance(data, np.ndarray))
        self.assertEqual(result_from_before,
                         self.TEST_APPLY_BEFORE_AFTER_MAGIC_NUMBER)

    def test_filters_populated(self):
        self.assertTrue(len(self.model.filter_names) > 0)

    def test_do_apply_filter(self):
        self.model.get_stack = lambda: self.sv_presenter

        self.model.execute = mock.MagicMock(
                return_value=self.multiply_execute_mock)

        self.model.do_apply_filter()

        self.model.execute.assert_called_once()

    def test_do_apply_filter_pre_post_processing(self):
        self.model.get_stack = lambda: self.sv_presenter

        self.model.execute = mock.MagicMock(
                return_value=self.multiply_execute_mock)

        self.model.do_before = mock.MagicMock(
                return_value=self.apply_before_mock)
        self.model.do_after = mock.MagicMock(
                return_value=self.apply_after_mock)

        self.model.do_apply_filter()

        self.model.execute.assert_called_once()

        self.model.do_before.assert_called_once()
        self.model.do_after.assert_called_once()


if __name__ == '__main__':
    unittest.main()
