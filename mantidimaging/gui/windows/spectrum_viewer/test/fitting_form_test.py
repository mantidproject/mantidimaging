# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations
import unittest
from unittest import mock

import numpy as np

from mantidimaging.gui.windows.spectrum_viewer.fitting_form import FittingFormWidgetPresenter


class FittingFormWidgetPresenterTest(unittest.TestCase):

    def setUp(self) -> None:
        self.view = mock.Mock()
        self.presenter = FittingFormWidgetPresenter(self.view)

    def test_show_initial_fit_calls_correct_plot_method(self):
        self.presenter.model = mock.Mock()
        self.view.fitting_param_form.get_initial_param_values = mock.Mock(return_value=[1.0, 2.0, 3.0, 4.0])
        self.presenter.model.tof_data = np.array([1, 2, 3])
        self.presenter.model.fitting_engine.model.evaluate = mock.Mock(return_value=np.array([10, 20, 30]))

        self.presenter.show_initial_fit()

        self.view.fittingDisplayWidget.show_fit_line.assert_called_once()
        args, kwargs = self.view.fittingDisplayWidget.show_fit_line.call_args
        np.testing.assert_array_equal(args[0], np.array([1, 2, 3]))
        np.testing.assert_array_equal(args[1], np.array([10, 20, 30]))
        assert kwargs["color"] == (128, 128, 128)
        assert kwargs["label"] == "initial"
        assert kwargs["initial"] is True
        self.view.fittingDisplayWidget.show_fit_line.reset_mock()
