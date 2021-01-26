import unittest
from unittest import mock

from mantidimaging.gui.widgets.palette_changer.presenter import PaletteChangerPresenter


class PaletteChangerPresenterTest(unittest.TestCase):
    def setUp(self) -> None:
        self.view = mock.MagicMock()
        self.presenter = PaletteChangerPresenter(self.view, None, None)
