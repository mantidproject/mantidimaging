# Copyright (C) 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from typing import List

from pyqtgraph import HistogramLUTItem
from skimage import filters

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
        self.old_ticks = list(self.hists[-1].gradient.ticks.keys())
        if self.view.algorithm == "Jenks":
            self._jenks_breaks()
        else:
            self._otsu_break()

    def _jenks_breaks(self):
        projection_hist = self.hists[-1]
        tick_points = self._generate_jenks_tick_points()
        # Insert new ticks
        for x in tick_points:
            projection_hist.gradient.addTick(x, finish=False)
        self._remove_old_ticks()
        self._update_ticks()

    def _change_colour_map(self):
        """
        Changes the colour map of the images.
        """
        preset = self.view.colour_map
        for hist in self.hists:
            hist.gradient.loadPreset(preset)

    def _otsu_break(self):
        val = filters.threshold_otsu(np.random.choice(self.projection_image.flatten(), 15000))
        tick = self._normalise_tick_values([val])[0]
        self.hists[-1].gradient.addTick(tick, finish=False)
        self._remove_old_ticks()
        self._update_ticks()

    def _generate_jenks_tick_points(self):
        """
        Generates tick points using the Jenks Breaks algorithm.
        """
        breaks = jenks_breaks(np.random.choice(self.projection_image.flatten(), 15000), self.view.num_materials)
        return self._normalise_tick_values(breaks)

    def _normalise_tick_values(self, breaks):
        min_val = self.projection_image.min()
        max_val = self.projection_image.max()
        val_range = abs(max_val - min_val)
        # Replace the first and last breaks, because the random may have missed them
        breaks[0], breaks[-1] = min_val, max_val
        # Normalise so the values range from 0 to 1
        for i in range(len(breaks)):
            breaks[i] = (breaks[i] - min_val) / val_range
        return breaks

    def _remove_old_ticks(self):
        for t in self.old_ticks:
            self.hists[-1].gradient.removeTick(t, finish=False)

    def _update_ticks(self):
        # Inform ticks object to update
        self.hists[-1].gradient.showTicks()
        self.hists[-1].gradient.sigGradientChangeFinished.emit(self.hists[-1].gradient)
