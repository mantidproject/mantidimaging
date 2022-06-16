# Copyright (C) 2022 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
import unittest
import uuid
from unittest import mock

from mantidimaging.core.data.dataset import StrictDataset, MixedDataset
from mantidimaging.gui.windows.main import MainWindowView
from mantidimaging.gui.windows.spectrum_viewer import SpectrumViewerWindowView
from mantidimaging.test_helpers import mock_versions, start_qapplication
from mantidimaging.test_helpers.unit_test_helper import generate_images


@mock_versions
@start_qapplication
class SpectrumViewerWindowViewTest(unittest.TestCase):
    def setUp(self) -> None:
        with mock.patch("mantidimaging.gui.windows.main.view.WelcomeScreenPresenter"):
            self.main_window = MainWindowView()
        self.main_window.get_dataset_id_from_stack_uuid = mock.Mock()
        self.main_window.get_dataset_id_from_stack_uuid.return_value = uuid.uuid4()
        self.view = SpectrumViewerWindowView(self.main_window)

    def test_handle_sample_change_has_flat_before(self):
        self.view.main_window.get_dataset_id_from_stack_uuid.return_value = uuid.uuid4()
        new_dataset = StrictDataset(generate_images(), flat_before=generate_images())
        new_dataset.flat_before.name = 'Flat_before'
        self.view.main_window.get_dataset = mock.Mock()
        self.view.main_window.get_dataset.return_value = new_dataset
        self.view.flatStackSelector.try_to_select_relevant_stack = mock.Mock()

        self.view._handle_sample_change(uuid.uuid4())
        self.view.flatStackSelector.try_to_select_relevant_stack.assert_called_once_with('Flat_before')

    def test_handle_sample_change_has_flat_after(self):
        self.view.main_window.get_dataset_id_from_stack_uuid.return_value = uuid.uuid4()
        new_dataset = StrictDataset(generate_images(), flat_after=generate_images())
        new_dataset.flat_after.name = 'Flat_after'
        self.view.main_window.get_dataset = mock.Mock()
        self.view.main_window.get_dataset.return_value = new_dataset
        self.view.flatStackSelector.try_to_select_relevant_stack = mock.Mock()

        self.view._handle_sample_change(uuid.uuid4())
        self.view.flatStackSelector.try_to_select_relevant_stack.assert_called_once_with('Flat_after')

    def test_handle_sample_change_no_new_stack(self):
        self.assertIsNotNone(self.view._current_dataset_id)
        self.view.flatStackSelector.try_to_select_relevant_stack = mock.Mock()

        self.view._handle_sample_change(None)
        self.view.flatStackSelector.try_to_select_relevant_stack.assert_not_called()
        self.assertIsNone(self.view._current_dataset_id)

    def test_handle_sample_change_dataset_unchanged(self):
        initial_dataset_id = self.view._current_dataset_id
        self.view.main_window.get_dataset = mock.Mock()

        self.view._handle_sample_change(uuid.uuid4())
        self.view.main_window.get_dataset.assert_not_called()
        self.assertEqual(self.view._current_dataset_id, initial_dataset_id)

    def test_handle_sample_change_to_MixedDataset(self):
        self.view.main_window.get_dataset_id_from_stack_uuid.return_value = uuid.uuid4()
        new_dataset = MixedDataset([generate_images()])
        self.view.main_window.get_dataset = mock.Mock()
        self.view.main_window.get_dataset.return_value = new_dataset
        self.view.flatStackSelector.try_to_select_relevant_stack = mock.Mock()

        self.view._handle_sample_change(uuid.uuid4())
        self.view.main_window.get_dataset.assert_called_once()
        self.view.flatStackSelector.try_to_select_relevant_stack.assert_not_called()

    def test_handle_sample_change_no_flat(self):
        self.view.main_window.get_dataset_id_from_stack_uuid.return_value = uuid.uuid4()
        new_dataset = StrictDataset(generate_images())
        self.view.main_window.get_dataset = mock.Mock()
        self.view.main_window.get_dataset.return_value = new_dataset
        self.view.flatStackSelector.try_to_select_relevant_stack = mock.Mock()

        self.view._handle_sample_change(uuid.uuid4())
        self.view.main_window.get_dataset.assert_called_once()
        self.view.flatStackSelector.try_to_select_relevant_stack.assert_not_called()
