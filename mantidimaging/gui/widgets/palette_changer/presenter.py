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
        tick_points = self._generate_jenks_tick_points()
        # Insert new ticks
        self._insert_new_ticks(tick_points)
        self._remove_old_ticks()
        self._update_ticks()

    def _insert_new_ticks(self, tick_points):
        """
        Adds new ticks to the projection histogram.
        """
        for x in tick_points:
            self.hists[-1].gradient.addTick(x, finish=False)

    def _change_colour_map(self):
        """
        Changes the colour map of the images.
        """
        preset = self.view.colour_map
        for hist in self.hists:
            hist.gradient.loadPreset(preset)

    def _otsu_break(self):
        val = filters.threshold_otsu(np.random.choice(self.projection_image.flatten(), 15000))
        ticks = self._normalise_tick_values([val])
        self._insert_new_ticks(ticks)
        self._remove_old_ticks()
        self._update_ticks()

    def _generate_jenks_tick_points(self):
        """
        Generates tick points using the Jenks Breaks algorithm.
        """
        breaks = jenks_breaks(np.random.choice(self.projection_image.flatten(), 15000), self.view.num_materials)
        # Replace the first and last breaks, because the random may have missed them
        return self._normalise_tick_values(list(breaks)[1:-1])

    def _normalise_tick_values(self, breaks):
        """
        Scale the collection of break values so that they range from 0 to 1.
        """
        min_val = self.projection_image.min()
        max_val = self.projection_image.max()
        val_range = abs(max_val - min_val)
        breaks = [min_val] + breaks + [max_val]
        # Normalise so the values range from 0 to 1
        for i in range(len(breaks)):
            breaks[i] = (breaks[i] - min_val) / val_range
        return breaks

    def _remove_old_ticks(self):
        """
        Remove the default projection histogram ticks from the image.
        """
        for t in self.old_ticks:
            self.hists[-1].gradient.removeTick(t, finish=False)

    def _update_ticks(self):
        """
        Tell the projection histogram ticks to update at the end of a change.
        """
        self.hists[-1].gradient.showTicks()
        self.hists[-1].gradient.sigGradientChangeFinished.emit(self.hists[-1].gradient)
