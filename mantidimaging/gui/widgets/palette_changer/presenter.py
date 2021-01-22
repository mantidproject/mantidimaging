# Copyright (C) 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from typing import List

from pyqtgraph import HistogramLUTItem

from mantidimaging.gui.mvp_base import BasePresenter
from jenkspy import jenks_breaks
import numpy as np


class PaletteChangerPresenter(BasePresenter):
    def __init__(self, view, hists: List[HistogramLUTItem], projection_image: np.ndarray):
        super(PaletteChangerPresenter, self).__init__(view)
        self.hists = hists
        self.projection_image = projection_image

    def notify(self, signal):
        pass

    def change_colour_palette(self):
        self._change_colour_map()
        if self.view.algorithm == "Jenks":
            self._jenks_breaks()
        else:
            self._otsu_break()

    def _jenks_breaks(self):
        hist = self.hists[-1]
        tick_points = self._generate_jenks_tick_points()
        old_ticks = list(hist.gradient.ticks.keys())
        for x in tick_points:
            hist.gradient.addTick(x, finish=False)
        for t in old_ticks:
            hist.gradient.removeTick(t, finish=False)
        hist.gradient.showTicks()
        hist.gradient.sigGradientChangeFinished.emit(hist.gradient)

    def _change_colour_map(self):
        preset = self.view.colour_map
        for hist in self.hists:
            hist.gradient.loadPreset(preset)

    def _otsu_break(self):
        pass

    def _generate_jenks_tick_points(self):
        breaks = jenks_breaks(np.random.choice(self.projection_image.flatten(), 15000), self.view.num_materials)
        min_val = self.projection_image.min()
        max_val = self.projection_image.max()
        val_range = abs(max_val - min_val)
        breaks[0], breaks[-1] = min_val, max_val
        for i in range(len(breaks)):
            breaks[i] = (breaks[i] - min_val) / val_range
        return breaks
