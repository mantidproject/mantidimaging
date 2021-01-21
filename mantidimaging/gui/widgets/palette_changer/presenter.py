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
        old_keys = list(hist.gradient.ticks.copy().keys())
        for tick_break in breaks:
            t = hist.gradient.addTick(tick_break, False)
        hist.gradient.updateGradient()
        hist.gradient.sigGradientChangeFinished.emit(self)
        # for tick in old_keys:
        #     hist.gradient.removeTick(tick)

    def _change_colour_map(self):
        preset = self.view.colour_map
        for hist in self.hists:
            hist.gradient.loadPreset(preset)

    def _otsu_break(self):
        pass
