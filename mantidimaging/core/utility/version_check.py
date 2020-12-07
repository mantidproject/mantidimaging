# Copyright (C) 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later

import json
import os
import subprocess
from logging import getLogger
from collections import namedtuple
import requests
from typing import Optional

from mantidimaging import __version__

LOG = getLogger(__name__)
ParsedVersion = namedtuple('ParsedVersion', ['version', 'commits'])

# Import as
#   from mantidimaging.core.utility.version_check import versions
# and use accessors
#   versions.get_conda_installed_version()
# Actual version lookups will only be performed once.


class CheckVersion:
    _conda_installed_version: Optional[str]
    _conda_installed_label: Optional[str]
    _conda_available_version: Optional[str]

    def __init__(self):
        self._version = __version__
        self._conda_installed_version = None
        self._conda_installed_label = None
        self._conda_available_version = None

        # To test update warning message uncomment
        # self._use_test_values(False)

    def _retrieve_versions(self) -> None:
        self._retrieve_conda_installed_version()
        self._retrieve_conda_available_version()

    def _use_test_values(self, uptodate: bool = True) -> None:
        """Avoid fetching version info"""
        self._conda_installed_version = "1.0.0_1"
        self._conda_installed_label = "main"
        if uptodate:
            self._conda_available_version = "1.0.0_1"
        else:
            self._conda_available_version = "2.0.0_1"

    def show_versions(self) -> None:
        print(f"Mantid imaging {self.get_version()}")
        print(f"conda_installed_version {self.get_conda_installed_version()}")
        print(f"conda_installed_label {self.get_conda_installed_label()}")
        print(f"conda_available_version {self.get_conda_available_version()}")

    def get_version(self) -> str:
        """Get built in version"""
        return self._version

    def get_conda_installed_version(self) -> Optional[str]:
        """Get version number of installed package from conda"""
        if self._conda_installed_version is None:
            self._retrieve_conda_installed_version()
        return self._conda_installed_version

    def get_conda_installed_label(self) -> Optional[str]:
        """Get with 'main' or 'unstable' from conda installed package"""
        if self._conda_installed_label is None:
            self._retrieve_conda_installed_version()
        return self._conda_installed_label

    def get_conda_available_version(self) -> Optional[str]:
        """Get latest version number from conda"""
        if self._conda_available_version is None:
            self._retrieve_conda_available_version()
        return self._conda_available_version

    def is_conda_uptodate(self) -> bool:
        """Check if up to date with lasted version in conda"""
        if (self.get_conda_installed_version() == "" or self.get_conda_available_version() == ""):
            # If unable to get conda versions then assume everything is good
            return True

        return _version_is_uptodate(_parse_version(self.get_conda_installed_version()),
                                    _parse_version(self.get_conda_available_version()))

    def conda_update_message(self) -> tuple:
        suffix = self.get_conda_installed_label()

        msg = f"Not running the latest Mantid Imaging{suffix}.\n"
        msg += f"Found version {self.get_conda_installed_version()}, "
        msg += f"latest: {self.get_conda_available_version()}.\nPlease check the terminal for an update command!"

        detailed = f"Not running the latest Mantid Imaging{suffix}.\n"
        detailed += f"Found version {self.get_conda_installed_version()}, "
        detailed += f"latest: {self.get_conda_available_version()}.\n"
        detailed += "To update your environment please copy and run the following command:\n"
        detailed += "source /opt/miniconda/bin/activate /opt/miniconda && "
        if self.get_conda_installed_label() != "main":
            detailed += "ENVIRONMENT_NAME=mantidimaging_unstable REPO_LABEL=unstable "
        detailed += "source "
        detailed += "<(curl -s https://raw.githubusercontent.com/mantidproject/mantidimaging/master/install.sh)"
        return msg, detailed

    def _retrieve_conda_installed_version(self) -> None:
        LOG.info("Finding and comparing mantidimaging versions")
        local_package = subprocess.check_output("conda list mantidimaging | grep '^[^#]' | awk 'END{print $2,$4}'",
                                                shell=True,
                                                env=os.environ).decode("utf-8").strip()
        if local_package == "":
            LOG.info("Running a development build without a local Mantid Imaging package installation.")
            # no local installation, no point sending out API requests
            # just returns as "unstable" label
            self._conda_installed_version = ""
            self._conda_installed_label = "unstable"
            return

        self._conda_installed_version, self._conda_installed_label = local_package.split()
        self._conda_installed_label = self._conda_installed_label.rpartition("/")[2]

    def _retrieve_conda_available_version(self) -> None:
        try:
            response = requests.get("https://api.anaconda.org/package/mantid/mantidimaging")
            remote_main_version = json.loads(response.content)["latest_version"]
            remote_unstable_version = json.loads(
                response.content)["versions"][-1] if len(json.loads(response.content)["versions"]) > 0 else ''
        except Exception:
            # if anything goes wrong, in the end we don't have the version
            LOG.info("Could not connect to Anaconda remote to retrieve the latest version")
            self._conda_available_version = ""
            return

        if self._conda_installed_label == "main":
            self._conda_available_version = remote_main_version
        else:
            self._conda_available_version = remote_unstable_version


versions = CheckVersion()


def _parse_version(package_version_string: Optional[str]) -> ParsedVersion:
    if package_version_string is None:
        raise ValueError
    local_version, local_commits_since_last = package_version_string.split("_")
    return ParsedVersion(tuple(map(int, local_version.split("."))), int(local_commits_since_last))


def _make_version_str(parsed: ParsedVersion) -> str:
    return f"{'.'.join([str(v) for v in parsed.version])}_{parsed.commits}"


def _version_is_uptodate(local: ParsedVersion, remote: ParsedVersion):
    if local.version < remote.version or local.commits < remote.commits:
        return False
    else:
        return True
