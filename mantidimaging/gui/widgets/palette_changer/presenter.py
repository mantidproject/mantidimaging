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
        # todo: log here
        preset = self.view.colour_map
        for hist in self.hists:
            hist.gradient.loadPreset(preset)
        self.hists[0].gradient.loadPreset("grey")
        # self.change_ticks(hist.gradient)
        # hist.gradient.ticks = [[]]
        for image in self.images:
            print(image.getHistogram())
            breaks = jenks_breaks(image.image[0], self.view.num_materials)
            print(breaks)
