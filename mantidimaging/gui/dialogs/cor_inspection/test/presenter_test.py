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
