# Copyright (C) 2024 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pyqtgraph import HistogramLUTItem
from skimage import filters

from mantidimaging.gui.mvp_base import BasePresenter
from jenkspy import jenks_breaks
import numpy as np
from math import pi

SAMPLE_SIZE = 15000  # Chosen to avoid Jenks becoming slow


class PaletteChangerPresenter(BasePresenter):

    def __init__(self, view, other_hists: list[HistogramLUTItem], main_hist: HistogramLUTItem, image: np.ndarray,
                 recon_mode: bool):
        super().__init__(view)
        self.rng = np.random.default_rng()
        self.other_hists = other_hists
        self.image = image
        self.main_hist = main_hist

        # Sample a subset of the histogram image to send to Jenks or Otsu
        if recon_mode:
            self.flattened_image = self._get_sample_pixels(self.image, min(SAMPLE_SIZE, image.size))
        else:
            self.flattened_image = self.rng.choice(image.flatten(), min(SAMPLE_SIZE, image.size))

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
        self.old_ticks = list(self.main_hist.gradient.ticks.keys())

    def _insert_new_ticks(self, tick_points: list[float]):
        """
        Adds new ticks to the recon histogram.
        """
        n_tick_points = len(tick_points)
        colours = self._get_colours(n_tick_points)
        for i in range(n_tick_points):
            self.main_hist.gradient.addTick(tick_points[i], color=colours[i], finish=False)

    def _change_colour_map(self):
        """
        Changes the colour map of all three histograms.
        """
        preset = self.view.colour_map
        for hist in self.other_hists + [self.main_hist]:
            hist.gradient.loadPreset(preset)

    def _generate_otsu_tick_points(self) -> list[float]:
        """
        Determine the Otsu threshold tick point.
        """
        vals = filters.threshold_multiotsu(self.image, classes=self.view.num_materials)
        return self._normalise_tick_values(vals.tolist())

    def _generate_jenks_tick_points(self) -> list[float]:
        """
        Determine the Jenks tick points.
        """
        breaks = jenks_breaks(self.flattened_image, self.view.num_materials)
        return self._normalise_tick_values(list(breaks)[1:-1])

    def _normalise_tick_values(self, breaks: list[float]) -> list[float]:
        """
        Scale the collection of break values so that they range from 0 to 1. This is done because addTick expects an
        x value in this range.
        """
        min_val = self.image.min()
        max_val = self.image.max()
        val_range = np.ptp(self.image)
        breaks = [min_val] + breaks + [max_val]
        return [(break_x - min_val) / val_range for break_x in breaks]

    def _remove_old_ticks(self):
        """
        Remove the default recon histogram ticks from the image.
        """
        for t in self.old_ticks:
            self.main_hist.gradient.removeTick(t, finish=False)

    def _update_ticks(self):
        """
        Tell the recon histogram ticks to update at the end of a change.
        """
        self.main_hist.gradient.showTicks()
        self.main_hist.gradient.updateGradient()
        self.main_hist.gradient.sigGradientChangeFinished.emit(self.main_hist.gradient)

    def _get_colours(self, num_ticks: int) -> list[float]:
        """
        Determine the colours that should be used for the new recon histogram ticks. Should ensure that there is a
        suitable amount of contrast between the different materials, even if the ticks are quite close together on
        the histogram.
        """
        norms = np.linspace(0, 1, num_ticks)
        return [self.main_hist.gradient.getColor(norm) for norm in norms]

    def _get_sample_pixels(self, image: np.ndarray, count: int, width: float = 0.9):
        """
        Sample from a circle of the image to avoid recon artefacts at edges
        """
        rs = self.rng.uniform(low=0, high=0.5 * width, size=count)
        thetas = self.rng.uniform(low=0, high=2 * pi, size=count)
        xs = (np.sin(thetas) * rs * image.shape[0] + image.shape[0] * 0.5).astype(int)
        ys = (np.cos(thetas) * rs * image.shape[1] + image.shape[1] * 0.5).astype(int)
        sampled = image[xs, ys]
        return sampled
