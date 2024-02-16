# Copyright (C) 2024 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

import shutil
import tempfile
import unittest


class FileOutputtingTestCase(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.output_directory = None

    def setUp(self):
        self.output_directory = tempfile.mkdtemp(prefix='mantidimaging_test_tmp_')

    def tearDown(self):
        shutil.rmtree(path=self.output_directory, ignore_errors=True)
