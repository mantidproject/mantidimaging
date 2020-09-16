import unittest

import mock
from testfixtures import LogCapture

from mantidimaging.gui.mvp_base import BaseDialogView, BaseMainWindowView, BasePresenter

class MIImageViewTest(unittest.TestCase):
    def test_one(self):
        MIImageView()