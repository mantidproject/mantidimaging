# Copyright (C) 2022 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
import unittest
import uuid
from unittest import mock

from mantidimaging.core.data.dataset import StrictDataset, MixedDataset
from mantidimaging.gui.windows.main import MainWindowView
from mantidimaging.gui.windows.spectrum_viewer import SpectrumViewerWindowView, SpectrumViewerWindowPresenter
from mantidimaging.gui.windows.spectrum_viewer.spectrum_widget import SpectrumWidget
from mantidimaging.test_helpers import mock_versions, start_qapplication
from mantidimaging.test_helpers.unit_test_helper import generate_images


@mock_versions
@start_qapplication
class SpectrumViewerWindowPresenterTest(unittest.TestCase):
    def setUp(self) -> None:
        with mock.patch("mantidimaging.gui.windows.main.view.WelcomeScreenPresenter"):
            self.main_window = MainWindowView()
        self.view = mock.create_autospec(SpectrumViewerWindowView)
        self.view.current_dataset_id = uuid.uuid4()
        self.view.spectrum = mock.create_autospec(SpectrumWidget)
        self.presenter = SpectrumViewerWindowPresenter(self.view, self.main_window)

    def test_get_dataset_id_for_stack_no_stack_id(self):
        self.assertIsNone(self.presenter.get_dataset_id_for_stack(None))

    def test_get_dataset_id_for_stack(self):
        self.main_window.get_dataset_id_from_stack_uuid = mock.Mock()

        self.presenter.get_dataset_id_for_stack(uuid.uuid4())
        self.main_window.get_dataset_id_from_stack_uuid.assert_called_once()

    def test_handle_sample_change_has_flat_before(self):
        self.presenter.get_dataset_id_for_stack = mock.Mock(return_value=uuid.uuid4())
        new_dataset = StrictDataset(generate_images([10, 11, 12]), flat_before=generate_images())
        new_dataset.flat_before.name = 'Flat_before'
        self.presenter.main_window.get_dataset = mock.Mock(return_value=new_dataset)
        self.presenter.main_window.get_stack = mock.Mock(return_value=generate_images())
        self.presenter.show_new_sample = mock.Mock()
        self.view.try_to_select_relevant_normalise_stack = mock.Mock()

        self.presenter.handle_sample_change(uuid.uuid4())
        self.view.try_to_select_relevant_normalise_stack.assert_called_once_with('Flat_before')
        self.presenter.show_new_sample.assert_called_once()

    def test_handle_sample_change_has_flat_after(self):
        self.presenter.get_dataset_id_for_stack = mock.Mock(return_value=uuid.uuid4())
        new_dataset = StrictDataset(generate_images(), flat_after=generate_images())
        new_dataset.flat_after.name = 'Flat_after'
        self.presenter.main_window.get_dataset = mock.Mock(return_value=new_dataset)
        self.presenter.main_window.get_stack = mock.Mock(return_value=generate_images())
        self.presenter.show_new_sample = mock.Mock()
        self.view.try_to_select_relevant_normalise_stack = mock.Mock()

        self.presenter.handle_sample_change(uuid.uuid4())
        self.view.try_to_select_relevant_normalise_stack.assert_called_once_with('Flat_after')
        self.presenter.show_new_sample.assert_called_once()

    def test_handle_sample_change_no_new_stack(self):
        self.presenter.get_dataset_id_for_stack = mock.Mock(return_value=None)
        self.view.try_to_select_relevant_normalise_stack = mock.Mock()
        self.presenter.show_new_sample = mock.Mock()

        self.presenter.handle_sample_change(None)
        self.view.try_to_select_relevant_normalise_stack.assert_not_called()
        self.assertIsNone(self.view.current_dataset_id)
        self.presenter.show_new_sample.assert_not_called()

    def test_handle_sample_change_dataset_unchanged(self):
        initial_dataset_id = self.view.current_dataset_id
        self.presenter.get_dataset_id_for_stack = mock.Mock(return_value=initial_dataset_id)
        self.presenter.main_window.get_dataset = mock.Mock()
        self.presenter.main_window.get_stack = mock.Mock(return_value=generate_images())
        self.presenter.show_new_sample = mock.Mock()

        self.presenter.handle_sample_change(uuid.uuid4())
        self.presenter.main_window.get_dataset.assert_not_called()
        self.assertEqual(self.view.current_dataset_id, initial_dataset_id)

    def test_handle_sample_change_to_MixedDataset(self):
        self.presenter.get_dataset_id_for_stack = mock.Mock(return_value=uuid.uuid4())
        new_dataset = MixedDataset([generate_images()])
        self.presenter.main_window.get_dataset = mock.Mock(return_value=new_dataset)
        self.presenter.main_window.get_stack = mock.Mock(return_value=generate_images())
        self.presenter.show_new_sample = mock.Mock()
        self.view.try_to_select_relevant_normalise_stack = mock.Mock()

        self.presenter.handle_sample_change(uuid.uuid4())
        self.presenter.main_window.get_dataset.assert_called_once()
        self.view.try_to_select_relevant_normalise_stack.assert_not_called()

    def test_handle_sample_change_no_flat(self):
        self.presenter.get_dataset_id_for_stack = mock.Mock(return_value=uuid.uuid4())
        new_dataset = StrictDataset(generate_images())
        self.presenter.main_window.get_dataset = mock.Mock(return_value=new_dataset)
        self.presenter.main_window.get_stack = mock.Mock(return_value=generate_images())
        self.presenter.show_new_sample = mock.Mock()
        self.view.try_to_select_relevant_normalise_stack = mock.Mock()

        self.presenter.handle_sample_change(uuid.uuid4())
        self.presenter.main_window.get_dataset.assert_called_once()
        self.view.try_to_select_relevant_normalise_stack.assert_not_called()

    def test_show_sample(self):
        image_stack = generate_images([10, 11, 12])
        self.view.spectrum.image = mock.Mock()
        self.view.spectrum.spectrum = mock.Mock()
        self.presenter.model.set_stack(image_stack)

        self.presenter.show_new_sample()
        self.view.spectrum.add_range.assert_called_once_with(0, 9)
