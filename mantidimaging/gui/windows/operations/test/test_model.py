# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later

import unittest
from functools import partial

from unittest import mock
import numpy as np

import mantidimaging.test_helpers.unit_test_helper as th
from mantidimaging.core.operation_history import const
from mantidimaging.gui.windows.operations import FiltersWindowModel
from mantidimaging.gui.windows.stack_visualiser import (StackVisualiserView, StackVisualiserPresenter, SVParameters)


class FiltersWindowModelTest(unittest.TestCase):
    APPLY_BEFORE_AFTER_MAGIC_NUMBER = 42
    ROI_PARAMETER = (4, 3, 2, 1)

    def __init__(self, *args, **kwargs):
        super(FiltersWindowModelTest, self).__init__(*args, **kwargs)

    @classmethod
    def setUpClass(cls):
        cls.test_data = th.generate_images()

    def setUp(self):
        self.sv_view = mock.create_autospec(StackVisualiserView)
        self.sv_view.current_roi = self.ROI_PARAMETER

        self.sv_presenter = StackVisualiserPresenter(self.sv_view, self.test_data)
        self.sv_view.presenter = self.sv_presenter

        self.model = FiltersWindowModel(mock.MagicMock())

    def execute_mock(self, data):
        self.assertTrue(isinstance(data, np.ndarray))
        data *= 4
        return data

    def execute_mock_with_roi(self, data, roi):
        self.assertTrue(isinstance(data, np.ndarray))
        data *= 4
        self.assertEqual(roi, self.ROI_PARAMETER)
        return data

    def setup_mocks(self, execute_mock):
        f = self.model.selected_filter
        orig_exec, orig_validate = f.execute_wrapper, f.validate_execute_kwargs
        self.model.setup_filter("", {})
        f.execute_wrapper = lambda: execute_mock
        f.validate_execute_kwargs = lambda _: True

        return orig_exec, orig_validate

    def reset_filter_model(self, exec, validate):
        f = self.model.selected_filter
        f.execute_wrapper = exec
        f.validate_execute_kwargs = validate

    @staticmethod
    def run_without_gui(task, on_complete):
        task()
        on_complete(None)

    def test_filters_populated(self):
        self.assertTrue(len(self.model.filter_names) > 0)

    @mock.patch("mantidimaging.gui.windows.operations.model.start_async_task_view")
    def test_do_apply_filter(self, mocked_start_view):
        mocked_start_view.side_effect = lambda _, task, on_complete: self.run_without_gui(task, on_complete)

        callback_mock = mock.Mock()

        def callback(arg):
            callback_mock()

        execute = mock.MagicMock(return_value=partial(self.execute_mock))
        originals = self.setup_mocks(execute)
        self.model.do_apply_filter([self.sv_view], callback)
        self.reset_filter_model(*originals)

        execute.assert_called_once()
        callback_mock.assert_called_once()

    @mock.patch("mantidimaging.gui.windows.operations.model.start_async_task_view")
    def test_do_apply_filter_with_roi(self, mocked_start_view):
        mocked_start_view.side_effect = lambda _, task, on_complete: self.run_without_gui(task, on_complete)

        callback_mock = mock.Mock()

        def callback(arg):
            callback_mock()

        execute = mock.MagicMock(return_value=partial(self.execute_mock_with_roi))
        originals = self.setup_mocks(execute)
        self.model.selected_filter.params = lambda: {'roi': SVParameters.ROI}
        self.model.do_apply_filter([self.sv_view], callback)
        self.reset_filter_model(*originals)

        execute.assert_called_once()
        callback_mock.assert_called_once()

    @mock.patch("mantidimaging.gui.windows.operations.model.start_async_task_view")
    def test_operation_recorded_in_image_history(self, mocked_start_view):
        mocked_start_view.side_effect = lambda _, task, on_complete: self.run_without_gui(task, on_complete)
        self.sv_presenter.images.metadata = {}

        callback_mock = mock.Mock()

        def callback(arg):
            callback_mock()

        execute = mock.MagicMock(return_value=partial(self.execute_mock))
        execute.args = ["arg"]
        execute.keywords = {"kwarg": "kwarg"}
        originals = self.setup_mocks(execute)

        self.model.do_apply_filter([self.sv_view], callback)
        self.reset_filter_model(*originals)

        op_history = self.sv_presenter.images.metadata['operation_history']
        self.assertEqual(len(op_history), 1, "One operation should have been recorded")
        self.assertEqual(op_history[0][const.OPERATION_KEYWORD_ARGS], {"kwarg": "kwarg"})
        # Recorded operation should not be a qualified module name.
        self.assertNotIn(".", op_history[0][const.OPERATION_NAME])
        callback_mock.assert_called_once()

    @mock.patch("mantidimaging.gui.windows.operations.model.FiltersWindowModel.apply_to_images")
    def test_apply_filter_to_stacks(self, apply_to_images_mock: mock.Mock):
        mock_stack_visualisers = [mock.Mock(), mock.Mock()]
        mock_progress = mock.Mock()

        self.model.apply_to_stacks(mock_stack_visualisers, mock_progress)

        apply_to_images_mock.assert_has_calls([
            mock.call(mock_stack_visualisers[0].presenter.images, progress=mock_progress),
            mock.call(mock_stack_visualisers[1].presenter.images, progress=mock_progress)
        ])

    def test_apply_filter_to_images(self):
        """
        When no 180deg projection is loaded the filter is only
        applied to the main data.
        """
        images = th.generate_images()
        selected_filter_mock = mock.Mock()
        selected_filter_mock.__name__ = mock.Mock()
        selected_filter_mock.__name__.return_value = "Test filter"
        selected_filter_mock.filter_name.return_value = "Test filter"
        progress_mock = mock.Mock()

        callback_mock = mock.Mock()

        selected_filter_mock.execute_wrapper.return_value = partial(callback_mock)
        self.model.selected_filter = selected_filter_mock
        self.model.apply_to_images(images, progress=progress_mock)

        selected_filter_mock.validate_execute_kwargs.assert_called_once()
        callback_mock.assert_called_once_with(images, progress=progress_mock)

    def test_get_filter_module_name(self):
        self.model.filters = mock.MagicMock()

        module_name = self.model.get_filter_module_name(0)

        self.assertEqual("unittest.mock", module_name)

    def test_find_filter_index_from_filter_name(self):
        filter1 = mock.MagicMock()
        filter1.filter_name = "1"
        filter2 = mock.MagicMock()
        filter2.filter_name = "2"
        filter3 = mock.MagicMock()
        filter3.filter_name = "3"
        self.model.filters = [filter1, filter2, filter3]

        self.assertEqual(1, self.model._find_filter_index_from_filter_name("2"))

    def test_filter_names(self):
        self.model.presenter.divider = "-----------------"
        filter_names = self.model.filter_names

        self.assertEqual([
            'Crop Coordinates', 'Flat-fielding', 'Remove Outliers', 'ROI Normalisation', "-----------------",
            'Arithmetic', 'Circular Mask', 'Clip Values', 'Divide', 'Gaussian', 'Median', 'Monitor Normalisation',
            'NaN Removal', 'Rebin', 'Rescale', 'Ring Removal', 'Rotate Stack', "-----------------",
            'Remove all stripes', 'Remove dead stripes', 'Remove large stripes', 'Stripe Removal',
            'Remove stripes with filtering', 'Remove stripes with sorting and fitting'
        ], filter_names)

    def test_find_drop_down_index_from_filter_name(self):
        for filter_name in self.model.filter_names:
            with self.subTest(filter_name=filter_name):
                index = self.model.find_drop_down_index_from_filter_name(filter_name)
                self.assertEqual(filter_name, self.model.filter_names[index])


if __name__ == '__main__':
    unittest.main()
