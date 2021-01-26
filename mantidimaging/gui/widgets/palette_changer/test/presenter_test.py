import unittest
from unittest import mock

import numpy as np
from pyqtgraph.graphicsItems import HistogramLUTItem

from mantidimaging.gui.widgets.palette_changer.presenter import PaletteChangerPresenter


class PaletteChangerPresenterTest(unittest.TestCase):
    def setUp(self) -> None:
        self.view = mock.MagicMock()
        self.histograms = [mock.Mock(spec=HistogramLUTItem) for _ in range(3)]
        self.projection_image = np.random.random((200, 200))
        self.presenter = PaletteChangerPresenter(self.view, self.histograms, self.projection_image)
