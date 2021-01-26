import unittest
from unittest import mock

import numpy as np

from mantidimaging.gui.widgets.palette_changer.presenter import PaletteChangerPresenter, RANDOM_CUTOFF


class PaletteChangerPresenterTest(unittest.TestCase):
    def setUp(self) -> None:
        self.view = mock.MagicMock()
        self.histograms = [mock.Mock() for _ in range(3)]
        self.projection_image = np.random.random((200, 200))
        self.presenter = PaletteChangerPresenter(self.view, self.histograms, self.projection_image)

    def test_flattened_image_creation_for_large_image(self):
        assert self.presenter.flattened_image.size == RANDOM_CUTOFF
        assert self.presenter.flattened_image.ndim == 1

    def test_flattened_image_creation_for_small_image(self):
        presenter = PaletteChangerPresenter(self.view, self.histograms, np.random.random((20, 20)))
        assert presenter.flattened_image.size == 400
        assert presenter.flattened_image.ndim == 1

    def test_change_colour_map(self):
        self.view.colour_map = colour_map_selection = "acolourmap"
        self.presenter._change_colour_map()

        for histogram in self.histograms:
            histogram.gradient.loadPreset.assert_called_once_with(colour_map_selection)
