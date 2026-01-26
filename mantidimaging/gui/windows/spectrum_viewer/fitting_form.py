# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations
from typing import TYPE_CHECKING
from logging import getLogger

import numpy as np
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton

from mantidimaging.gui.widgets.spectrum_widgets.fitting_selection_widget import FitSelectionWidget
from mantidimaging.gui.widgets.spectrum_widgets.roi_selection_widget import ROISelectionWidget
from mantidimaging.gui.widgets.spectrum_widgets.fitting_param_form_widget import FittingParamFormWidget

if TYPE_CHECKING:
    from mantidimaging.gui.windows.spectrum_viewer import SpectrumViewerWindowView

LOG = getLogger(__name__)


class FittingFormWidgetView(QWidget):
    """
    Widget for the form area of the fitting tab

    Contains widgets for selecting fitting model and parameters
    """

    def __init__(self, spectrum_viewer: SpectrumViewerWindowView):
        super().__init__(None)
        self.spectrum_viewer = spectrum_viewer
        self.presenter = FittingFormWidgetPresenter(self)
        self.setLayout(QVBoxLayout())

        self.roiSelectionWidget = ROISelectionWidget(self)
        self.layout().addWidget(self.roiSelectionWidget)

        self.fitSelectionWidget = FitSelectionWidget(self)
        self.layout().addWidget(self.fitSelectionWidget)

        self.fitting_param_form = FittingParamFormWidget(self.spectrum_viewer.presenter)
        self.layout().addWidget(self.fitting_param_form)

        self.run_fit_button = QPushButton("Run fit")
        self.layout().addWidget(self.run_fit_button)
        self.run_fit_button.clicked.connect(self.presenter.run_region_fit)

        self.rss_label = QLabel("RSS:")
        self.reduced_rss_label = QLabel("RSS/DoF:")
        self.layout().addWidget(self.rss_label)
        self.layout().addWidget(self.reduced_rss_label)

        self.layout().addStretch()

        self.fittingDisplayWidget = spectrum_viewer.fittingDisplayWidget

        self.roiSelectionWidget.selectionChanged.connect(self.presenter.handle_roi_selection_changes)
        self.fitSelectionWidget.selectionChanged.connect(self.presenter.update_fitting_function)
        self.fitting_param_form.fromROIButtonClicked.connect(self.presenter.get_init_params_from_roi)
        self.fitting_param_form.initialEditFinished.connect(self.presenter.on_initial_params_edited)

    def showEvent(self, ev) -> None:
        super().showEvent(ev)
        self.presenter.handle_activated()

    @property
    def current_roi_name(self) -> str:
        return self.roiSelectionWidget.current_roi_name

    def set_fit_quality(self, rss: float, rss_per_dof: float) -> None:
        """
        Update the fit quality display with raw and reduced residual sum of squares.
        """
        self.rss_label.setText(f"RSS: {rss:.2g}")
        self.reduced_rss_label.setText(f"RSS/DoF: {rss_per_dof:.2g}")


class FittingFormWidgetPresenter:
    """
    Presenter for the fitting tab

    Handles the behaviour of the fitting tab
    """

    def __init__(self, view: FittingFormWidgetView):
        self.view = view
        self.spectrum_viewer = view.spectrum_viewer
        self.model = self.spectrum_viewer.presenter.model
        self.fitting_display_widget = view.spectrum_viewer.fittingDisplayWidget
        self.first_activation = True

    @property
    def fitting_spectrum(self) -> tuple[np.ndarray, np.ndarray]:
        selected_fitting_roi = self.view.current_roi_name
        if (spectrum_data := self.spectrum_viewer.spectrum_widget.spectrum_data_dict[selected_fitting_roi]) is not None:
            return self.model.tof_data, spectrum_data

        raise RuntimeError("Fitting spectrum not calculated")

    def handle_activated(self) -> None:
        LOG.warning("Fitting form activated")
        self.update_roi_dropdown()
        self.update_roi_on_fitting_thumbnail()
        self.set_spectrum()
        self.set_default_fitting_region()
        self.set_binning()
        if self.first_activation:
            self.setup_fitting_model()
            self.first_activation = False

    def handle_roi_selection_changes(self) -> None:
        self.update_roi_on_fitting_thumbnail()
        self.set_spectrum()

    def set_spectrum(self) -> None:
        spectrum_data = self.fitting_spectrum
        self.fitting_display_widget.update_plot(*spectrum_data)

    def update_roi_dropdown(self) -> None:
        roi_names = self.spectrum_viewer.presenter.get_roi_names()
        self.view.roiSelectionWidget.update_roi_list(roi_names)

    def update_roi_on_fitting_thumbnail(self) -> None:
        roi_widget = self.spectrum_viewer.spectrum_widget.roi_dict[self.view.roiSelectionWidget.current_roi_name]
        self.spectrum_viewer.fittingDisplayWidget.show_roi_on_thumbnail_from_widget(roi_widget)

    def set_default_fitting_region(self) -> None:
        self.view.fittingDisplayWidget.set_default_region_if_needed(*self.fitting_spectrum)

    def set_binning(self) -> None:
        mode = self.spectrum_viewer.presenter.export_mode
        binner = self.spectrum_viewer.get_binner()
        self.view.roiSelectionWidget.handle_mode_change(mode)
        self.view.roiSelectionWidget.handle_binning_changed(binner)

    def update_fitting_function(self, fitting_obj) -> None:
        fitting_func = fitting_obj()
        self.model.fitting_engine.set_fitting_model(fitting_func)
        LOG.info("Spectrum Viewer: Fit function set to %s", fitting_func.__class__.__name__)
        self.setup_fitting_model()

    def setup_fitting_model(self) -> None:
        param_names = self.model.fitting_engine.get_parameter_names()
        self.view.fitting_param_form.set_parameters(param_names)
        self.spectrum_viewer.exportDataTableWidget.set_parameters(param_names)

    def get_init_params_from_roi(self) -> None:
        fitting_region = self.fitting_display_widget.get_selected_fit_region()
        init_params = self.model.fitting_engine.get_init_params_from_roi(fitting_region)
        self.view.fitting_param_form.set_parameter_values(init_params)

        self.view.fittingDisplayWidget.set_plot_mode("initial")

        self.show_initial_fit()
        roi_name = self.view.roiSelectionWidget.current_roi_name
        self.view.set_fit_quality(float("nan"), float("nan"))
        self.spectrum_viewer.exportDataTableWidget.update_roi_data(
            roi_name=roi_name,
            params=init_params,
            status="Initial",
            chi2=None,
        )

    def show_fit(self, params: list[float]) -> None:
        xvals = self.model.tof_data
        fit = self.model.fitting_engine.model.evaluate(xvals, params)
        self.view.fittingDisplayWidget.show_fit_line(xvals, fit, color=(0, 128, 255), label="fit", initial=False)

    def show_initial_fit(self) -> None:
        """
        Displays the initial fit curve on the fitting display widget.
        Retrieves current TOF data and the initial parameter values from the view
        and evaluates the fitting model using these parameters to generate the initial fit curve.
        """
        xvals = self.model.tof_data
        init_params = self.view.fitting_param_form.get_initial_param_values()
        init_fit = self.model.fitting_engine.model.evaluate(xvals, init_params)
        self.view.fittingDisplayWidget.show_fit_line(xvals,
                                                     init_fit,
                                                     color=(128, 128, 128),
                                                     label="initial",
                                                     initial=True)

    def on_initial_params_edited(self) -> None:
        """
        Handles updates when the initial fitting parameters are edited.

        If the initial fit is visible, updates the plot with the new initial fit.
        Otherwise, re-runs the fit with the updated parameters, updates the fitted parameter values,
        and displays the new fit result.
        """
        if self.view.fittingDisplayWidget.is_initial_fit_visible():
            self.show_initial_fit()
        else:
            init_params = self.view.fitting_param_form.get_initial_param_values()
            roi_name = self.view.roiSelectionWidget.current_roi_name
            roi = self.spectrum_viewer.spectrum_widget.get_roi(roi_name)
            spectrum = self.model.get_spectrum(roi, self.spectrum_viewer.presenter.spectrum_mode)
            xvals = self.model.tof_data
            bound_params = self.view.fitting_param_form.get_bound_parameters()
            fit_params, rss, rss_per_dof = self.model.fitting_engine.find_best_fit(xvals,
                                                                                   spectrum,
                                                                                   init_params,
                                                                                   params_bounds=bound_params)
            self.view.fitting_param_form.set_fitted_parameter_values(fit_params)
            self.view.set_fit_quality(rss, rss_per_dof)
            self.show_fit(list(fit_params.values()))
            LOG.info("Refit completed for ROI=%s, RSS/DoF=%.3f", roi_name, rss_per_dof)

    def run_region_fit(self) -> None:
        """
        Run a fit on the currently selected ROI and update the GUI/export table.
        """
        bound_params = self.view.fitting_param_form.get_bound_parameters()
        tof_data, spectrum = self.fitting_spectrum
        result, rss, reduced_rss = self.model.fit_single_region(spectrum,
                                                                self.spectrum_viewer.get_fitting_region(),
                                                                tof_data,
                                                                self.view.fitting_param_form.get_initial_param_values(),
                                                                bounds=bound_params)
        self.view.fitting_param_form.set_fitted_parameter_values(result)
        self.view.set_fit_quality(rss, reduced_rss)
        self.show_fit(list(result.values()))
        roi_name = self.view.roiSelectionWidget.current_roi_name
        self.spectrum_viewer.exportDataTableWidget.update_roi_data(
            roi_name=roi_name,
            params=result,
            status="Fitted",
            chi2=reduced_rss,
        )
        LOG.info("Fit completed for ROI=%s, params=%s, RSS/DoF=%.3f", roi_name, result, reduced_rss)
