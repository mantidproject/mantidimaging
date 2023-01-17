# Copyright (C) 2022 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations
from typing import Optional, TYPE_CHECKING, List

from PyQt5.QtWidgets import QAction

from mantidimaging.gui.widgets.palette_changer.view import PaletteChangerView

if TYPE_CHECKING:
    from pyqtgraph import HistogramLUTItem
    import numpy as np
    from PyQt5.QtWidgets import QWidget

DEFAULT_MENU_POSITION = 12


class AutoColorMenu:
    """
    Mixin class to be used with MIImageView and MIMiniImageView
    """
    def __init__(self) -> None:
        self.auto_color_action: Optional[QAction] = None

    @property
    def histogram(self) -> 'HistogramLUTItem':
        raise NotImplementedError('Required histogram property not implemented')

    @property
    def image_data(self) -> 'np.ndarray':
        raise NotImplementedError('Required image_data property not implemented')

    @property
    def other_histograms(self) -> 'List[HistogramLUTItem]':
        return []

    def add_auto_color_menu_action(self,
                                   parent: 'Optional[QWidget]',
                                   recon_mode: bool = False,
                                   index: int = DEFAULT_MENU_POSITION,
                                   set_enabled: bool = True) -> QAction:
        self.auto_color_action = QAction("Auto")
        place = self.histogram.gradient.menu.actions()[index]

        self.histogram.gradient.menu.insertAction(place, self.auto_color_action)
        self.histogram.gradient.menu.insertSeparator(self.auto_color_action)
        self.set_auto_color_enabled(set_enabled)
        self.auto_color_action.triggered.connect(lambda: self._on_colour_change_palette(parent, recon_mode))

        return self.auto_color_action

    def set_auto_color_enabled(self, enabled: bool = True) -> None:
        if self.auto_color_action is not None:
            self.auto_color_action.setEnabled(enabled)

    def _on_colour_change_palette(self, parent: 'Optional[QWidget]', recon_mode: bool) -> None:
        """
        Opens the Palette Changer window
        """
        change_colour_palette = PaletteChangerView(parent=parent,
                                                   main_hist=self.histogram,
                                                   image=self.image_data,
                                                   other_hists=self.other_histograms,
                                                   recon_mode=recon_mode)
        change_colour_palette.show()
