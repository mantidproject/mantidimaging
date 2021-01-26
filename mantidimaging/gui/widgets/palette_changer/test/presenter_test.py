import unittest
from unittest import mock

import numpy as np

from mantidimaging.gui.widgets.palette_changer.presenter import PaletteChangerPresenter, RANDOM_CUTOFF


class PaletteChangerPresenterTest(unittest.TestCase):
    def setUp(self) -> None:
        self.view = mock.MagicMock()
        self.histograms = [mock.Mock() for _ in range(3)]
        self.projection_histogram = self.histograms[-1]
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

    def test_record_old_tick_points(self):
        old_ticks_list = [mock.Mock() for i in range(2)]
        self.projection_histogram.gradient.ticks = {old_ticks_list[i]: i * 1.0 for i in range(2)}
        self.presenter._record_old_tick_points()
        assert self.presenter.old_ticks == old_ticks_list

    def test_insert_new_ticks(self):
        pass

    def test_change_colour_palette(self):
        pass

    def test_get_colours(self):
        self.projection_histogram.gradient.getColor = get_color_mock = mock.Mock()
        n_ticks = 5
        colours = self.presenter._get_colours(n_ticks)
        get_color_mock.assert_has_calls([mock.call(x) for x in np.linspace(0, 1, n_ticks)])
        for colour in colours:
            assert colour == get_color_mock.return_value

    @mock.patch("mantidimaging.gui.widgets.palette_changer.presenter.filters.threshold_otsu")
    def test_generate_otsu_tick_points(self, threshold_otsu_mock):
        threshold_otsu_mock.return_value = otsu_value = np.random.choice(self.presenter.flattened_image)
        norm_otsu = (otsu_value - self.projection_image.min()) / abs(self.projection_image.max() -
                                                                     self.projection_image.min())
        self.assertListEqual(self.presenter._generate_otsu_tick_points(), [0.0, norm_otsu, 1.0])

    def test_generate_jenks_tick_points(self):
        pass
