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


class FittingParamFormWidgetView(QWidget):

    def __init__(self, spectrum_viewer: SpectrumViewerWindowView):
        super().__init__(None)
        self.spectrum_viewer = spectrum_viewer
        self.presenter = FittingParamFormWidgetPresenter(self)
        self.setLayout(QVBoxLayout())

        self.roiSelectionWidget = ROISelectionWidget(self)
        self.layout().addWidget(self.roiSelectionWidget)

        self.fitSelectionWidget = FitSelectionWidget(self)
        self.layout().addWidget(self.fitSelectionWidget)

        self.fitting_param_form = FittingParamFormWidget(self.spectrum_viewer.presenter)
        self.layout().addWidget(self.fitting_param_form)

        self.run_fit_button = QPushButton("Run fit")
        self.layout().addWidget(self.run_fit_button)
        self.run_fit_button.clicked.connect(self.spectrum_viewer.presenter.run_region_fit)

        self.rss_label = QLabel("RSS:")
        self.reduced_rss_label = QLabel("RSS/DoF:")
        self.layout().addWidget(self.rss_label)
        self.layout().addWidget(self.reduced_rss_label)

        self.layout().addStretch()

        self.fittingDisplayWidget = spectrum_viewer.fittingDisplayWidget

        self.roiSelectionWidget.selectionChanged.connect(self.presenter.handle_roi_selection_changes)

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


class FittingParamFormWidgetPresenter:

    def __init__(self, view: FittingParamFormWidgetView):
        self.view = view
        self.spectrum_viewer = view.spectrum_viewer
        self.fitting_display_widget = view.spectrum_viewer.fittingDisplayWidget

    @property
    def fitting_spectrum(self) -> tuple[np.ndarray, np.ndarray]:
        selected_fitting_roi = self.view.current_roi_name
        if (spectrum_data := self.spectrum_viewer.spectrum_widget.spectrum_data_dict[selected_fitting_roi]) is not None:
            return self.spectrum_viewer.presenter.model.tof_data, spectrum_data

        raise RuntimeError("Fitting spectrum not calculated")

    def handle_activated(self) -> None:
        LOG.warning("Fitting form activated")
        self.update_roi_dropdown()
        self.update_roi_on_fitting_thumbnail()
        self.set_spectrum()
        self.set_default_fitting_region()
        self.set_binning()

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
