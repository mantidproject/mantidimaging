# Copyright (C) 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later

import unittest
from unittest import mock
from unittest.mock import call

from mantidimaging.core.utility.data_containers import ScalarCoR, ReconstructionParameters, Degrees
from mantidimaging.gui.dialogs.cor_inspection import CORInspectionDialogPresenter
import mantidimaging.test_helpers.unit_test_helper as th
from mantidimaging.gui.dialogs.cor_inspection.presenter import Notification
from mantidimaging.gui.dialogs.cor_inspection.types import ImageType


class CORInspectionDialogPresenterTest(unittest.TestCase):
    @mock.patch("mantidimaging.gui.dialogs.cor_inspection.presenter.CORInspectionDialogModel")
    def setUp(self, model) -> None:
        self.view = mock.MagicMock()
        self.model = model.return_value
        self.recon_params = ReconstructionParameters("", "", 0, ScalarCoR(2), Degrees(2), 2, 2)
        self.presenter = CORInspectionDialogPresenter(self.view, th.generate_images(), 5, ScalarCoR(2),
                                                      self.recon_params, False)

    def test_init_sets_get_title(self):
        with mock.patch("mantidimaging.gui.dialogs.cor_inspection.CORInspectionDialogModel"):
            presenter = CORInspectionDialogPresenter(self.view, th.generate_images(), 5, ScalarCoR(2),
                                                     self.recon_params, True)
            assert "Iterations" in presenter.get_title(ImageType.CURRENT)

            presenter = CORInspectionDialogPresenter(self.view, th.generate_images(), 5, ScalarCoR(2),
                                                     self.recon_params, False)
            assert "COR" in presenter.get_title(ImageType.CURRENT)

    def test_click_less(self):
        with self.assertLogs(self.presenter.__module__, level='DEBUG') as presenter_log:
            self.presenter.notify(Notification.IMAGE_CLICKED_LESS)
        self.model.adjust.assert_called_once_with(ImageType.LESS)
        self.assertIn("Image selected: {}".format(ImageType.LESS), presenter_log.output[0])

        assert self.view.step_size == self.model.step
        calls = [
            call(image, self.model.recon_preview.return_value, self.presenter.get_title(image)) for image in ImageType
        ]
        self.view.set_image.assert_has_calls(calls)

    def test_click_current(self):
        with self.assertLogs(self.presenter.__module__, level='DEBUG') as presenter_log:
            self.presenter.notify(Notification.IMAGE_CLICKED_CURRENT)
        self.model.adjust.assert_called_once_with(ImageType.CURRENT)
        self.assertIn("Image selected: {}".format(ImageType.CURRENT), presenter_log.output[0])

        assert self.view.step_size == self.model.step
        calls = [
            call(image, self.model.recon_preview.return_value, self.presenter.get_title(image)) for image in ImageType
        ]
        calls.pop(1)
        self.view.set_image.assert_has_calls(calls)

    def test_click_more(self):
        with self.assertLogs(self.presenter.__module__, level='DEBUG') as presenter_log:
            self.presenter.notify(Notification.IMAGE_CLICKED_MORE)
        self.model.adjust.assert_called_once_with(ImageType.MORE)
        self.assertIn("Image selected: {}".format(ImageType.MORE), presenter_log.output[0])

        assert self.view.step_size == self.model.step
        calls = [
            call(image, self.model.recon_preview.return_value, self.presenter.get_title(image)) for image in ImageType
        ]
        self.view.set_image.assert_has_calls(calls)

    def test_full_update_refreshes(self):
        self.presenter.notify(Notification.FULL_UPDATE)
        calls = [
            call(image, self.model.recon_preview.return_value, self.presenter.get_title(image)) for image in ImageType
        ]
        self.view.set_image.assert_has_calls(calls)

    def test_update_parameters(self):
        self.presenter.notify(Notification.UPDATE_PARAMETERS_FROM_UI)
        assert self.model.step == self.view.step_size
        calls = [
            call(image, self.model.recon_preview.return_value, self.presenter.get_title(image)) for image in ImageType
        ]
        self.view.set_image.assert_has_calls(calls)

    def test_on_load(self):
        self.presenter.notify(Notification.LOADED)
        self.view.set_maximum_cor.assert_called_once_with(self.model.cor_extents.__getitem__.return_value)

    def test_exception_logs_failure(self):
        self.presenter.on_load = mock.Mock(side_effect=Exception)
        with self.assertLogs(self.presenter.__module__, level='ERROR') as presenter_log:
            self.presenter.notify(Notification.LOADED)
        self.assertIn("Notification handler failed", presenter_log.output[0])

    @mock.patch('mantidimaging.gui.dialogs.cor_inspection.presenter.ScalarCoR')
    def test_optimal_rotation_centre(self, scalar_cor_mock):
        assert self.presenter.optimal_rotation_centre == scalar_cor_mock.return_value
        scalar_cor_mock.assert_called_once_with(self.model.centre_value)

    def test_optimal_iterations(self):
        assert self.presenter.optimal_iterations == self.model.centre_value
