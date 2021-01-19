# Copyright (C) 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later

from mantidimaging.gui.mvp_base import BasePresenter


class PaletteChangerPresenter(BasePresenter):
    def __init__(self, view, hists):
        super(PaletteChangerPresenter, self).__init__(view)
        self.hists = hists

    def notify(self, signal):
        pass

    def change_colour_palette(self):
        # todo: log here
        preset = self.view.colour_map
        for hist in self.hists:
            hist.gradient.loadPreset(preset)
