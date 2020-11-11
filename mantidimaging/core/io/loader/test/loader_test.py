# Copyright (C) 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later

import unittest

from mantidimaging.core.io import loader


class LoaderTest(unittest.TestCase):
    def test_raise_on_invalid_format(self):
        self.assertRaises(ValueError, loader.load, "/some/path", file_names=["/somefile"], in_format='txt')
