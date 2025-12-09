# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations
from typing import TYPE_CHECKING
from logging import getLogger

import numpy as np
from PyQt5.QtWidgets import QWidget, QVBoxLayout

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

        self.fittingDisplayWidget = spectrum_viewer.fittingDisplayWidget

        self.roiSelectionWidget.selectionChanged.connect(self.presenter.update_roi_on_fitting_thumbnail)

    def showEvent(self, ev) -> None:
        super().showEvent(ev)
        self.presenter.handle_activated()


class FittingParamFormWidgetPresenter:

    def __init__(self, view: FittingParamFormWidgetView):
        self.view = view
        self.spectrum_viewer = view.spectrum_viewer

    @property
    def fitting_spectrum(self) -> np.ndarray:
        selected_fitting_roi = self.view.roiSelectionWidget.current_roi_name
        if (spectrum_data := self.spectrum_viewer.spectrum_widget.spectrum_data_dict[selected_fitting_roi]) is not None:
            return spectrum_data

        raise RuntimeError("Fitting spectrum not calculated")

    def handle_activated(self) -> None:
        LOG.warning("Fitting form activated")
        self.update_roi_dropdown()
        self.update_roi_on_fitting_thumbnail()
        self.set_default_fitting_region()

    def update_roi_dropdown(self) -> None:
        roi_names = self.spectrum_viewer.presenter.get_roi_names()
        self.view.roiSelectionWidget.update_roi_list(roi_names)

    def update_roi_on_fitting_thumbnail(self) -> None:
        roi_widget = self.spectrum_viewer.spectrum_widget.roi_dict[self.view.roiSelectionWidget.current_roi_name]
        self.spectrum_viewer.fittingDisplayWidget.show_roi_on_thumbnail_from_widget(roi_widget)

    def set_default_fitting_region(self) -> None:
        self.view.fittingDisplayWidget.set_default_region_if_needed(self.spectrum_viewer.presenter.model.tof_data,
                                                                    self.fitting_spectrum)
