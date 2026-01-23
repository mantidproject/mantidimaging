# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations
import unittest
from unittest import mock

import numpy as np
from parameterized import parameterized

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

    @parameterized.expand([
        (True, True, False),  # (is_initial_fit_visible, expect_plot_initial, expect_show_fit)
        (False, False, True),
    ])
    def test_on_initial_params_edited_updates_plot_correctly(self, is_initial_fit_visible, expect_plot_initial,
                                                             expect_show_fit):
        self.presenter.show_initial_fit = mock.Mock()
        self.view.fittingDisplayWidget.show_fit_line = mock.Mock()
        self.view.fitting_param_form.get_initial_param_values = mock.Mock(return_value=[1.0, 2.0, 3.0, 4.0])
        self.view.roiSelectionWidget.current_roi_name = "roi"
        self.view.spectrum_widget.get_roi = mock.Mock(return_value="mock_roi")
        self.presenter.model.get_spectrum = mock.Mock(return_value=np.array([1, 2, 3]))
        self.presenter.model.tof_data = np.array([1, 2, 3])
        self.presenter.model.fitting_engine.find_best_fit = mock.Mock(return_value=(
            {
                "mu": 1.0,
                "sigma": 2.0,
                "h": 3.0,
                "a": 4.0,
            },
            0.0,
            0.0,
        ))
        self.view.fitting_param_form.set_fitted_parameter_values = mock.Mock()
        self.view.fittingDisplayWidget.is_initial_fit_visible.return_value = is_initial_fit_visible

        self.presenter.on_initial_params_edited()

        if expect_plot_initial:
            self.presenter.show_initial_fit.assert_called_once()
            self.view.fittingDisplayWidget.show_fit_line.assert_not_called()
            self.view.fitting_param_form.set_fitted_parameter_values.assert_not_called()
        if expect_show_fit:
            self.presenter.show_initial_fit.assert_not_called()
            self.view.fittingDisplayWidget.show_fit_line.assert_called_once()
            args, kwargs = self.view.fittingDisplayWidget.show_fit_line.call_args
            np.testing.assert_array_equal(args[0], np.array([1, 2, 3]))
            assert kwargs["color"] == (0, 128, 255)
            assert kwargs["label"] == "fit"
            assert kwargs["initial"] is False
            self.view.fitting_param_form.set_fitted_parameter_values.assert_called_once_with({
                "mu": 1.0,
                "sigma": 2.0,
                "h": 3.0,
                "a": 4.0
            })

    @parameterized.expand([
        ([1.0, 2.0], [10, 20, 30], [100, 200, 300]),
        ([0.5, 1.5], [5, 15, 25], [50, 150, 250]),
    ])
    def test_show_fit_calls_show_fit_line_with_expected_args(self, fitted_params, xvals, fit):
        xvals = np.array(xvals)
        fit = np.array(fit)
        self.presenter.model.tof_data = xvals
        self.presenter.model.fitting_engine.model.evaluate = mock.Mock(return_value=fit)
        self.view.fittingDisplayWidget.show_fit_line = mock.Mock()

        self.presenter.show_fit(fitted_params)

        self.presenter.model.fitting_engine.model.evaluate.assert_called_once_with(xvals, fitted_params)
        self.view.fittingDisplayWidget.show_fit_line.assert_called_once_with(xvals,
                                                                             fit,
                                                                             color=(0, 128, 255),
                                                                             label="fit",
                                                                             initial=False)
