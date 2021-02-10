# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from typing import List

from pyqtgraph import HistogramLUTItem
from skimage import filters

from mantidimaging.gui.mvp_base import BasePresenter
from jenkspy import jenks_breaks
import numpy as np

RANDOM_CUTOFF = 15000


class PaletteChangerPresenter(BasePresenter):
    def __init__(self, view, hists: List[HistogramLUTItem], recon_image: np.ndarray):
        super(PaletteChangerPresenter, self).__init__(view)
        self.hists = hists
        self.recon_image = recon_image
        self.recon_histogram = hists[0]
        # Create a flattened version of the histogram image to send to Jenks or Otsu
        if recon_image.size > RANDOM_CUTOFF:
            # Use a random subset if the image is large
            self.flattened_image = np.random.choice(self.recon_image.flatten(), RANDOM_CUTOFF)
        else:
            # Use the entire array if the image is small
            self.flattened_image = self.recon_image.flatten()

    def notify(self, signal):
        pass

    def change_colour_palette(self):
        """
        Change the colour palette and add ticks based on the output of the Jenks or Otsu algorithms.
        """
        self._change_colour_map()
        self._record_old_tick_points()
        if self.view.algorithm == "Jenks":
            tick_points = self._generate_jenks_tick_points()
        else:
            tick_points = self._generate_otsu_tick_points()
        self._insert_new_ticks(tick_points)
        self._remove_old_ticks()
        self._update_ticks()

    def _record_old_tick_points(self):
        """
        Records the default tick points for the recon histogram that are inserted when a new colour map is loaded.
        This means they can be easily removed once the new ticks have been added to the histogram. This step is
        carried out because the method for determining a new tick's colour fails if there are no ticks present. Hence,
        these are only removed after the new Otsu/Jenks ticks have already been placed in the histogram.
        """
        self.old_ticks = list(self.recon_histogram.gradient.ticks.keys())

    def _insert_new_ticks(self, tick_points: List[float]):
        """
        Adds new ticks to the recon histogram.
        """
        n_tick_points = len(tick_points)
        colours = self._get_colours(n_tick_points)
        for i in range(n_tick_points):
            self.recon_histogram.gradient.addTick(tick_points[i], color=colours[i], finish=False)

    def _change_colour_map(self):
        """
        Changes the colour map of all three histograms.
        """
        preset = self.view.colour_map
        for hist in self.hists:
            hist.gradient.loadPreset(preset)

    def _generate_otsu_tick_points(self) -> List[float]:
        """
        Determine the Otsu threshold tick point.
        """
        vals = filters.threshold_multiotsu(self.recon_image, classes=self.view.num_materials)
        return self._normalise_tick_values(vals.tolist())

    def _generate_jenks_tick_points(self) -> List[float]:
        """
        Determine the Jenks tick points.
        """
        breaks = jenks_breaks(self.flattened_image, self.view.num_materials)
        return self._normalise_tick_values(list(breaks)[1:-1])

    def _normalise_tick_values(self, breaks: List[float]) -> List[float]:
        """
        Scale the collection of break values so that they range from 0 to 1. This is done because addTick expects an
        x value in this range.
        """
        min_val = self.recon_image.min()
        max_val = self.recon_image.max()
        val_range = np.ptp(self.recon_image)
        breaks = [min_val] + breaks + [max_val]
        return [(break_x - min_val) / val_range for break_x in breaks]

    def _remove_old_ticks(self):
        """
        Remove the default recon histogram ticks from the image.
        """
        for t in self.old_ticks:
            self.recon_histogram.gradient.removeTick(t, finish=False)

    def _update_ticks(self):
        """
        Tell the recon histogram ticks to update at the end of a change.
        """
        self.recon_histogram.gradient.showTicks()
        self.recon_histogram.gradient.updateGradient()
        self.recon_histogram.gradient.sigGradientChangeFinished.emit(self.recon_histogram.gradient)

    def _get_colours(self, num_ticks: int) -> List[float]:
        """
        Determine the colours that should be used for the new recon histogram ticks. Should ensure that there is a
        suitable amount of contrast between the different materials, even if the ticks are quite close together on
        the histogram.
        """
        norms = np.linspace(0, 1, num_ticks)
        return [self.recon_histogram.gradient.getColor(norm) for norm in norms]
