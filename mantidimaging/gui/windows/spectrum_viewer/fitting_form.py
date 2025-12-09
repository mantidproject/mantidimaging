# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations
from typing import TYPE_CHECKING
from logging import getLogger

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
        self.presenter = FittingParamFormWidgetPresenter(self)
        self.setLayout(QVBoxLayout())

        self.spectrum_viewer = spectrum_viewer
        self.roiSelectionWidget = ROISelectionWidget(self)
        self.layout().addWidget(self.roiSelectionWidget)

        self.fitSelectionWidget = FitSelectionWidget(self)
        self.layout().addWidget(self.fitSelectionWidget)

        self.fitting_param_form = FittingParamFormWidget(self.spectrum_viewer.presenter)
        self.layout().addWidget(self.fitting_param_form)

    def showEvent(self, ev) -> None:
        super().showEvent(ev)
        self.presenter.handle_activated()


class FittingParamFormWidgetPresenter:

    def __init__(self, view: FittingParamFormWidgetView):
        self.view = view

    def handle_activated(self) -> None:
        LOG.warning("Fitting form activated")
