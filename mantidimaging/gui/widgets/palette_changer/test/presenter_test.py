import unittest
from unittest import mock

import numpy as np

from mantidimaging.gui.widgets.palette_changer.presenter import PaletteChangerPresenter, RANDOM_CUTOFF


def _normalise_break_value(break_value, min_value, max_value):
    return (break_value - min_value) / abs(max_value - min_value)


class PaletteChangerPresenterTest(unittest.TestCase):
    def setUp(self) -> None:
        self.view = mock.MagicMock()
        self.histograms = [mock.Mock() for _ in range(3)]
        self.projection_histogram = self.histograms[-1]
        self.projection_image = np.random.random((200, 200))
        self.projection_gradient = self.projection_histogram.gradient
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
        self.assertListEqual(self.presenter.old_ticks, old_ticks_list)

    def test_insert_new_ticks(self):
        tick_locations = [i * 0.1 for i in range(11)]
        self.presenter._insert_new_ticks(tick_locations)
        self.projection_gradient.addTick.assert_has_calls(
            [mock.call(x, color=self.projection_gradient.getColor.return_value, finish=False) for x in tick_locations])

    def test_get_colours(self):
        get_color_mock = self.projection_histogram.gradient.getColor
        n_ticks = 5
        colours = self.presenter._get_colours(n_ticks)
        get_color_mock.assert_has_calls([mock.call(x) for x in np.linspace(0, 1, n_ticks)])
        for colour in colours:
            assert colour == get_color_mock.return_value

    @mock.patch("mantidimaging.gui.widgets.palette_changer.presenter.filters.threshold_otsu")
    def test_generate_otsu_tick_points(self, threshold_otsu_mock):
        threshold_otsu_mock.return_value = otsu_value = np.random.choice(self.presenter.flattened_image)
        norm_otsu = _normalise_break_value(otsu_value, self.projection_image.min(), self.projection_image.max())
        self.assertListEqual(self.presenter._generate_otsu_tick_points(), [0.0, norm_otsu, 1.0])

    @mock.patch("mantidimaging.gui.widgets.palette_changer.presenter.jenks_breaks")
    def test_generate_jenks_tick_points(self, jenks_breaks_mocks):
        self.view.num_materials = n_breaks = 4
        jenks_breaks_mocks.return_value = expected_jenks_ticks = sorted(
            (np.random.choice(self.presenter.flattened_image) for _ in range(n_breaks)))
        expected_jenks_ticks = list(
            map(
                lambda break_value: _normalise_break_value(
                    break_value, min_value=self.projection_image.min(), max_value=self.projection_image.max()),
                expected_jenks_ticks))
        expected_jenks_ticks[0] = 0.0
        expected_jenks_ticks[-1] = 1.0
        actual_tick_points = self.presenter._generate_jenks_tick_points()
        jenks_breaks_mocks.assert_called_once_with(self.presenter.flattened_image, n_breaks)
        self.assertListEqual(expected_jenks_ticks, actual_tick_points)

    def test_remove_old_ticks(self):
        n_old_ticks = 3
        self.presenter.old_ticks = mock_old_ticks = [mock.Mock() for _ in range(n_old_ticks)]
        self.presenter._remove_old_ticks()
        self.projection_gradient.removeTick.assert_has_calls([mock.call(t, finish=False) for t in mock_old_ticks])

    def test_update_ticks(self):
        self.presenter._update_ticks()
        self.projection_gradient.showTicks.assert_called_once()
        self.projection_gradient.updateGradient.assert_called_once()
        self.projection_gradient.sigGradientChangeFinished.emit.assert_called_once_with(self.projection_gradient)
