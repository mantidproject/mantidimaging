# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

from abc import abstractmethod, ABC
from typing import TYPE_CHECKING

from PyQt5.QtWidgets import QAction

from mantidimaging.gui.utility.qt_helpers import _metaclass_sip_abc
from mantidimaging.gui.widgets.palette_changer.view import PaletteChangerView

if TYPE_CHECKING:
    from pyqtgraph import HistogramLUTItem
    import numpy as np
    from PyQt5.QtWidgets import QWidget


class AutoColorMenu(ABC, metaclass=_metaclass_sip_abc):
    """
    Mixin class to be used with MIImageView and MIMiniImageView
    """

    def __init__(self) -> None:
        super().__init__()
        self.auto_color_action: QAction | None = None

    @property
    @abstractmethod
    def histogram(self) -> HistogramLUTItem:
        ...

    @property
    @abstractmethod
    def image_data(self) -> np.ndarray | None:
        ...

    @property
    def other_histograms(self) -> list[HistogramLUTItem]:
        return []

    def add_auto_color_menu_action(self,
                                   parent: QWidget | None,
                                   recon_mode: bool = False,
                                   set_enabled: bool = True) -> QAction:
        self.auto_color_parent = parent
        self.auto_color_recon_mode = recon_mode
        self.auto_color_action = QAction("Auto")

        index_of_rgb_item = [action.text() for action in self.histogram.gradient.menu.actions()].index("RGB")
        place = self.histogram.gradient.menu.actions()[index_of_rgb_item - 1]

        self.histogram.gradient.menu.insertAction(place, self.auto_color_action)
        self.histogram.gradient.menu.insertSeparator(self.auto_color_action)
        self.set_auto_color_enabled(set_enabled)
        self.auto_color_action.triggered.connect(self._on_colour_change_palette)

        return self.auto_color_action

    def set_auto_color_enabled(self, enabled: bool = True) -> None:
        if self.auto_color_action is not None:
            self.auto_color_action.setEnabled(enabled)

    def _on_colour_change_palette(self) -> None:
        """
        Opens the Palette Changer window
        """
        change_colour_palette = PaletteChangerView(parent=self.auto_color_parent,
                                                   main_hist=self.histogram,
                                                   image=self.image_data,
                                                   other_hists=self.other_histograms,
                                                   recon_mode=self.auto_color_recon_mode)
        change_colour_palette.show()
