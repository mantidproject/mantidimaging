# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations
from math import isnan

import numpy as np
from PyQt5 import QtCore
from pyqtgraph import GraphicsLayoutWidget, InfiniteLine, ScatterPlotItem, mkBrush, mkPen

from mantidimaging.core.utility.close_enough_point import CloseEnoughPoint
from mantidimaging.core.utility.data_containers import Degrees
from mantidimaging.core.utility.histogram import set_histogram_log_scale
from mantidimaging.gui.widgets.line_profile_plot.view import LineProfilePlot
from mantidimaging.gui.widgets.mi_mini_image_view.view import MIMiniImageView


class ReconImagesView(GraphicsLayoutWidget):
    sigSliceIndexChanged = QtCore.pyqtSignal(int)
    sigCorPointClicked = QtCore.pyqtSignal(int)

    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self._selected_cor_row: int = -1  # Default to no row selected
        self._scatter_rows: list[int] = []
        self._scatter_cors: list[float] = []
        self._scatter_slice_indices: list[int] = []
        self._tilt_value: float = 0.0

        self.imageview_projection = MIMiniImageView(name="Projection", parent=parent)
        self.imageview_sinogram = MIMiniImageView(name="Sinogram", parent=parent)
        self.imageview_recon = MIMiniImageView(name="Recon", parent=parent, recon_mode=True)

        self.slice_line = InfiniteLine(pos=1024, angle=0, movable=True)
        self.imageview_projection.viewbox.addItem(self.slice_line)
        self.tilt_line = InfiniteLine(pos=1024, angle=90, pen=(255, 0, 0, 255), movable=False)
        self._normal_pen = mkPen((255, 255, 0, 255), width=1)
        self._hover_pen = mkPen((0, 255, 255, 255), width=3)
        self._selected_pen = mkPen((0, 255, 0, 255), width=2)
        self._normal_brush = mkBrush(255, 255, 0, 200)
        self._selected_brush = mkBrush(0, 255, 0, 200)
        self.cor_scatter = ScatterPlotItem(symbol='x',
                                           size=14,
                                           pen=self._normal_pen,
                                           hoverable=True,
                                           hoverPen=self._hover_pen)
        self.cor_scatter.sigHovered.connect(self._on_cor_scatter_hovered)
        self.imageview_projection.viewbox.addItem(self.cor_scatter)
        self.cor_scatter.sigClicked.connect(self._on_cor_scatter_clicked)
        self.recon_line_profile = LineProfilePlot(self.imageview_recon)

        self.addItem(self.imageview_projection, 0, 0)
        self.addItem(self.imageview_sinogram, 1, 0)

        self.recon_layout = self.ci.addLayout(0, 1, rowspan=2)
        self.recon_layout.addItem(self.imageview_recon, 0, 0)
        self.recon_layout.addItem(self.recon_line_profile, 1, 0)
        # Set the recon preview to take up more vertical space than the line profile graph underneath it
        self.recon_layout.layout.setRowStretchFactor(0, 2)

        self.imageview_projection.image_item.mouseClickEvent = lambda ev: self.mouse_click(ev, self.slice_line)
        self.slice_line.sigPositionChangeFinished.connect(self.slice_line_moved)

        # Work around for https://github.com/mantidproject/mantidimaging/issues/565
        self.scene().contextMenu = [item for item in self.scene().contextMenu if "export" not in item.text().lower()]

        self.imageview_projection.enable_nan_check()
        self.imageview_sinogram.enable_nan_check()
        self.imageview_recon.enable_nan_check()
        self.imageview_projection.enable_value_check()
        self.imageview_sinogram.enable_value_check()

    def cleanup(self) -> None:
        self.imageview_projection.cleanup()
        self.imageview_sinogram.cleanup()
        self.imageview_recon.cleanup()
        self.recon_line_profile.cleanup()
        del self.imageview_projection
        del self.imageview_sinogram
        del self.imageview_recon

    def slice_line_moved(self) -> None:
        self.slice_changed(int(self.slice_line.value()))

    def update_projection(self, image_data: np.ndarray, preview_slice_index: int) -> None:
        self.imageview_projection.clear()
        self.imageview_projection.setImage(image_data)
        self.imageview_projection.histogram.imageChanged(autoLevel=True, autoRange=True)
        self.slice_line.setPos(preview_slice_index)
        self.slice_line.setBounds([0, int(self.imageview_projection.image_item.height()) - 1])
        set_histogram_log_scale(self.imageview_projection.histogram)

    def update_sinogram(self, image) -> None:
        self.imageview_sinogram.clear()
        self.imageview_sinogram.setImage(image)
        self.imageview_sinogram.histogram.imageChanged(autoLevel=True, autoRange=True)
        set_histogram_log_scale(self.imageview_sinogram.histogram)

    def update_recon(self, image_data, reset_roi: bool = False) -> None:
        self.imageview_recon.clear()
        self.imageview_recon.setImage(image_data, autoLevels=False)
        set_histogram_log_scale(self.imageview_recon.histogram)
        if reset_roi:
            self.recon_line_profile.reset()
        else:
            self.recon_line_profile.update()

    def update_recon_hist(self) -> None:
        self.imageview_recon.histogram.imageChanged(autoLevel=True, autoRange=True)

    def mouse_click(self, ev, line: InfiniteLine) -> None:
        line.setPos(ev.pos())
        self.slice_changed(CloseEnoughPoint(ev.pos()).y)

    def slice_changed(self, slice_index) -> None:
        self.parent.presenter.do_preview_reconstruct_slice(slice_idx=slice_index)
        self.sigSliceIndexChanged.emit(slice_index)

    def clear_recon(self) -> None:
        self.imageview_recon.clear()

    def clear_recon_line_profile(self) -> None:
        self.recon_line_profile.clear_plot()

    def clear_sinogram(self) -> None:
        self.imageview_sinogram.clear()

    def clear_projection(self) -> None:
        self.imageview_projection.clear()

    def reset_slice_and_tilt(self, slice_index) -> None:
        self.slice_line.setPos(slice_index)
        self.hide_cor_line()

    def hide_cor_line(self) -> None:
        """
        Hides the tilt line. This stops infinite zooming out loop that messes up the image view
        (the line likes to be unbound when the degree isn't a multiple o 90 - and the tilt never is)
        :return:
        """
        if self.tilt_line.scene() is not None:
            self.imageview_projection.viewbox.removeItem(self.tilt_line)

    def update_cor_table_points(self, slice_indices: list[int], cors: list[float], tilt: float = 0.0) -> None:
        """
        Updates the CoR scatter points on the projection preview and the tilt line if there is a tilt

        :param slice_indices: list of slice indices for the CoR points
        :param cors: list of CoR values for the CoR points
        :param tilt: tilt value for the tilt line, if there is a tilt
        """
        self._tilt_value = tilt
        self._scatter_cors = cors
        self._scatter_slice_indices = slice_indices
        self._scatter_rows = list(range(len(slice_indices)))
        self._refresh_cor_scatter()

    def set_selected_cor_row(self, row: int) -> None:
        self._selected_cor_row = row
        self._refresh_cor_scatter()

    def _make_spot(self, cor: float, slice_idx: int, row: int) -> dict:
        """
        Create CoR spot and update its appearance based on whether it is selected or not

        :param cor: CoR value
        :param slice_idx: slice index
        :param row: row index
        :return: dict of spot parameters
        """
        selected = row == self._selected_cor_row
        return {
            'pos': (cor, slice_idx),
            'data': row,
            'pen': self._selected_pen if selected else self._normal_pen,
            'brush': self._selected_brush if selected else self._normal_brush,
        }

    def _refresh_cor_scatter(self) -> None:
        """Update scatter plot with current CoR by creating a list of spots and setting them to the scatter plot item"""
        cor_table_data = zip(self._scatter_cors, self._scatter_slice_indices, self._scatter_rows, strict=True)
        spots = [self._make_spot(cor, slice_idx, row) for cor, slice_idx, row in cor_table_data]
        self.cor_scatter.setData(spots=spots, symbol='x', size=14, tip=None)

    def _on_cor_scatter_clicked(self, plot, spots, ev) -> None:
        if spots:
            row_index_from_cor_spot = spots[0].data()
            self.sigCorPointClicked.emit(row_index_from_cor_spot)

    def _on_cor_scatter_hovered(self, plot: ScatterPlotItem, points: list) -> None:
        if plot_canvas := plot.getViewWidget():
            plot_canvas.setCursor(QtCore.Qt.OpenHandCursor if points else QtCore.Qt.ArrowCursor)

    def show_cor_line(self, tilt: Degrees, pos: float) -> None:
        if not isnan(tilt.value):  # is isnan it means there is no tilt, i.e. the line is vertical
            self.tilt_line.setPos((pos, 0))
            self.tilt_line.setAngle(90 + tilt.value)
        self.imageview_projection.viewbox.addItem(self.tilt_line)

    def reset_recon_histogram(self) -> None:
        self.imageview_recon.histogram.autoHistogramRange()
