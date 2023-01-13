# Copyright (C) 2022 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

from parameterized import parameterized
import unittest
from unittest import mock

from mantidimaging.core.utility.version_check import (CheckVersion, _version_is_uptodate, _parse_version)
from mantidimaging.test_helpers import mock_versions


@mock_versions
class TestCheckVersion(unittest.TestCase):
    def setUp(self):
        with mock.patch("mantidimaging.core.utility.version_check.CheckVersion._retrieve_versions"):
            with mock.patch("shutil.which"):
                self.versions = CheckVersion()
                self.versions._version = "1.0.0.post1"
                self.versions._conda_available_version = "1.0.0.post1"

    @parameterized.expand([["9.9.9_1234"], ["9.9.9.post1234"]])
    def test_parse_version(self, version_string):
        parsed = _parse_version(version_string)

        self.assertEqual(parsed.release, (9, 9, 9))
        self.assertEqual(parsed.post, 1234)

    def test_parse_version_no_commits(self):
        parsed = _parse_version("9.9.9")

        self.assertEqual(parsed.release, (9, 9, 9))

    def test_parse_version_release_candidate(self):
        parsed = _parse_version("9.9.9rc")

        self.assertEqual(parsed.release, (9, 9, 9))
        self.assertEqual(parsed.pre, ("rc", 0))

    def test_parse_version_release_candidate_with_commits(self):
        parsed = _parse_version("9.9.9rc.post2")

        self.assertEqual(parsed.release, (9, 9, 9))
        self.assertEqual(parsed.pre, ("rc", 0))
        self.assertEqual(parsed.post, 2)

    @parameterized.expand([
        ["8.9.9_1234", "9.9.9_1234", False],
        ["9.9.9_1234", "19.9.9_1234", False],
        ["9.9.9_1234", "19.9.9_0", False],
        ["9.9.9_1", "9.9.9_2", False],
        ["8.9.9_1234", "8.9.9_1234", True],
        ["9.9.9_1234", "8.9.9_1234", True],
        ["8.9.9_2000", "8.9.9_1234", True],
        ["8.10.9_1234", "8.9.9_1234", True],
        ["1.1.0rc_18", "1.1.0_18", False],
        ["1.1.0a_18", "1.1.0_18", False],
        ["1.1.0a_18", "1.1.0rc_18", False],
        ["1.1.0rc_18", "1.1.0a_19", True],
        ["1.1.0a1_18", "1.1.0a1_19", False],
        ["1.1.0a1_18", "1.1.0a1.post19", False],
    ])
    def test_version_is_uptodate(self, local, remote, is_uptodate):
        self.assertEqual(_version_is_uptodate(local, remote), is_uptodate)

    def test_needs_update(self):
        self.assertFalse(self.versions.needs_update())

    @parameterized.expand([
        ["1.0.0", False],
        ["1.1.0", True],
    ])
    def test_needs_update_conda(self, available, needed):
        self.versions._version = "1.0.0"
        self.versions._package_type = "conda"
        self.versions._conda_available_version = available

        self.assertEqual(self.versions.needs_update(), needed)

    @parameterized.expand([
        ["1.0.0", False],
        ["1.0.0a1", True],
        ["1.0.0a1.post1", True],
    ])
    def test_version_is_prerelease(self, version, prerelease):
        self.versions._version = version

        self.assertEqual(self.versions.is_prerelease(), prerelease)

    def test_conda_update_message(self):
        self.versions._conda_available_version = "2.0.0"
        msg, detailed = self.versions.conda_update_message()
        self.assertTrue("Found version 1.0.0.post1" in msg)
        self.assertTrue("latest: 2.0.0" in msg)
        self.assertTrue("To update your environment" in detailed)

    @mock.patch("builtins.print")
    def test_show_versions(self, mock_print):
        self.versions.show_versions()
        mock_print.assert_called()

    @mock.patch("requests.get")
    def test_retrieve_conda_available_version(self, mock_get):
        mock_get.return_value = mock.Mock(content='{"latest_version": "1.1.0_1018", "versions": ["1.1.0_1090"]}')
        self.versions._version = "1.0.0"
        self.versions._retrieve_conda_available_version()
        self.assertEqual(self.versions.get_conda_available_version(), "1.1.0_1018")

        self.versions._version = "1.0.0a1"
        self.versions._retrieve_conda_available_version()
        self.assertEqual(self.versions.get_conda_available_version(), "1.1.0_1090")

    @parameterized.expand([
        [{
            "mamba": "path_to_mamba",
            "conda": "path_to_conda"
        }, "mamba"],
        [{
            "mamba": None,
            "conda": "path_to_conda"
        }, "conda"],
        [{
            "mamba": None,
            "conda": None
        }, None],
    ])
    @mock.patch("shutil.which")
    def test_find_conda_executable(self, mock_values, expected, mock_which):
        mock_which.side_effect = lambda arg: mock_values[arg]

        if expected:
            self.assertEqual(self.versions.find_conda_executable(), expected)
        else:
            self.assertRaises(FileNotFoundError, self.versions.find_conda_executable)
