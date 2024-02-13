# Copyright (C) 2024 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

from mantidimaging.core.operations.loader import load_filter_packages
from mantidimaging.test_helpers.unit_test_helper import FakeFSTestCase
from pathlib import Path

from mantidimaging.eyes_tests.base_eyes import BaseEyesTest

filters = {f.filter_name: f for f in load_filter_packages()}  # Needed for pyfakefs


class LiveViewerWindowTest(FakeFSTestCase, BaseEyesTest):

    def setUp(self) -> None:
        super().setUp()
        self.fs.add_real_directory(Path(__file__).parent.parent)

    def test_live_view_opens_without_data(self):
        self.fs.create_dir("/live_dir")
        self.imaging.show_live_viewer(Path("/live_dir"))
        self.check_target(widget=self.imaging.live_viewer)
