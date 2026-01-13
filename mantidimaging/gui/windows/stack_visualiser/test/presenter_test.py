# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

import unittest
from unittest import mock
from unittest.mock import patch

from mantidimaging.gui.windows.stack_visualiser.presenter import SVParameters

import mantidimaging.test_helpers.unit_test_helper as th
from mantidimaging.core.data import ImageStack
from mantidimaging.gui.windows.stack_visualiser import StackVisualiserPresenter, StackVisualiserView, SVNotification, \
    SVImageMode
from mantidimaging.test_helpers.unit_test_helper import generate_angles


class StackVisualiserPresenterTest(unittest.TestCase):
    test_data: ImageStack

    def setUp(self):
        self.test_data = th.generate_images()
        # mock the view so it has the same methods
        self.view = mock.create_autospec(StackVisualiserView, instance=True)
        self.presenter = StackVisualiserPresenter(self.view, self.test_data)
        test_angles = generate_angles(360, self.presenter.images.num_projections)
        self.presenter.images.set_projection_angles(test_angles)
        self.presenter.model = mock.Mock()
        self.view._main_window = mock.Mock()

    def test_delete_data(self):
        self.presenter.images = th.generate_images()
        self.presenter.delete_data()
        self.assertIsNone(self.presenter.images, None)

    def test_notify_refresh_image_normal_image_mode(self):
        self.presenter.image_mode = SVImageMode.NORMAL
        self.presenter.notify(SVNotification.REFRESH_IMAGE)
        self.view.set_image.assert_called_with(self.presenter.images)

    def test_notify_refresh_image_averaged_image_mode(self):
        self.presenter.image_mode = SVImageMode.SUMMED
        mock_summed = mock.Mock()
        self.presenter.model.sum_images.return_value = mock_summed
        self.presenter.notify(SVNotification.REFRESH_IMAGE)
        self.presenter.model.sum_images.assert_called_with(self.presenter.images)
        self.assertIs(self.view.image, mock_summed, "Image should have been set as averaged image")

    @mock.patch('mantidimaging.gui.windows.stack_visualiser.presenter.StackVisualiserPresenter.refresh_image')
    def test_notify_toggle_image_mode_normal_to_summed(self, mock_refresh):
        self.presenter.image_mode = SVImageMode.SUMMED
        self.presenter.notify(SVNotification.TOGGLE_IMAGE_MODE)
        assert self.presenter.image_mode is SVImageMode.NORMAL
        mock_refresh.assert_called_once()
        self.presenter.model.sum_images.assert_not_called()

    @mock.patch('mantidimaging.gui.windows.stack_visualiser.presenter.StackVisualiserPresenter.refresh_image')
    def test_notify_toggle_image_mode_summed_to_normal(self, mock_refresh):
        self.presenter.image_mode = SVImageMode.NORMAL
        self.presenter.notify(SVNotification.TOGGLE_IMAGE_MODE)
        assert self.presenter.image_mode is SVImageMode.SUMMED
        mock_refresh.assert_called_once()
        self.presenter.model.sum_images.assert_not_called()

    def test_get_num_images(self):
        assert self.presenter.get_num_images() == self.presenter.images.num_projections

    @patch("mantidimaging.gui.windows.stack_visualiser.presenter.getLogger")
    def test_notify_exception_log(self, get_logger_mock):
        self.presenter.refresh_image = mock.Mock()
        self.presenter.refresh_image.side_effect = Exception

        self.presenter.notify(SVNotification.REFRESH_IMAGE)
        get_logger_mock.return_value.exception.assert_called_once_with("Notification handler failed")

    def test_get_parameter_value_returns_roi(self):
        assert self.presenter.get_parameter_value(SVParameters.ROI) == self.presenter.view.current_roi

    def test_get_parameter_value_raises_value_error(self):
        with self.assertRaises(ValueError):
            self.presenter.get_parameter_value(7)

    def test_add_sinograms_to_model_and_update_view(self):
        sinograms = th.generate_images()
        self.presenter.add_sinograms_to_model_and_update_view(sinograms)
        self.view._main_window.presenter.add_sinograms_to_dataset_and_update_view.assert_called_once_with(
            sinograms, self.presenter.images.id)


if __name__ == '__main__':
    unittest.main()
