# Copyright (C) 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later

from mantidimaging.gui.mvp_base import BasePresenter
from jenkspy import jenks_breaks


class PaletteChangerPresenter(BasePresenter):
    def __init__(self, view, hists, images):
        super(PaletteChangerPresenter, self).__init__(view)
        self.hists = hists
        self.images = images

    def notify(self, signal):
        pass

    def change_colour_palette(self):
        self._change_colour_map()
        if self.view.algorithm == "Jenks":
            self._jenks_breaks()
        else:
            self._otsu_break()

    def _jenks_breaks(self):
        image = self.images[-1]
        hist = self.hists[-1]
        breaks = jenks_breaks(image.image[0], self.view.num_materials)
        levels = hist.getLevels()
        breaks[0] = levels[0]
        breaks[-1] = levels[1]
        norm = 1.0 / abs(levels[1] - levels[0])
        breaks = [(b + levels[0]) * norm for b in breaks]
        old_ticks = list(hist.gradient.ticks.keys())
        for tick_break in breaks:
            t = hist.gradient.addTick(tick_break, finish=False)
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
