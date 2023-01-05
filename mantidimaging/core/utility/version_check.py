# Copyright (C) 2022 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later

import json
import os
import subprocess
import sys
from logging import getLogger
import requests
from typing import Optional
from packaging import version
import shutil

try:
    from mantidimaging.versions import package_version, git_hash, package_type  # type: ignore
except ImportError:
    package_version = '0.0.0.dev1'
    git_hash = ''
    package_type = ''

LOG = getLogger(__name__)

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
        self._version = package_version
        self._conda_installed_version = None
        self._conda_installed_label = None
        self._conda_available_version = None
        self._conda_exe = self.find_conda_executable()

    def _retrieve_versions(self) -> None:
        self._retrieve_conda_installed_version()
        self._retrieve_conda_available_version()

    @staticmethod
    def find_conda_executable() -> str:
        if shutil.which("mamba"):
            return "mamba"
        if shutil.which("conda"):
            return "conda"
        raise FileNotFoundError

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

    def needs_update(self) -> bool:
        if not self.is_conda_uptodate():
            return True
        return False

    def is_conda_uptodate(self) -> bool:
        """Check if up to date with lasted version in conda"""
        if (self.get_conda_installed_version() == "" or self.get_conda_available_version() == ""):
            # If unable to get conda versions then assume everything is good
            return True

        return _version_is_uptodate(_parse_version(self.get_conda_installed_version()),
                                    _parse_version(self.get_conda_available_version()))

    def conda_update_message(self) -> tuple:
        suffix = self.get_conda_installed_label()

        msg = "Not running the latest Mantid Imaging"
        if suffix != "main":
            msg += f"-{suffix}"
        msg += f".\nFound version {self.get_conda_installed_version()}, "
        msg += f"latest: {self.get_conda_available_version()}.\nPlease check the terminal for an update command!"

        detailed = f"Not running the latest Mantid Imaging {suffix}.\n"
        detailed += f"Found version {self.get_conda_installed_version()}, "
        detailed += f"latest: {self.get_conda_available_version()}.\n"
        detailed += "To update your environment please copy and run the following command:\n"
        if sys.platform == 'linux':
            detailed += f"{self._conda_exe} activate {os.environ['CONDA_PREFIX']} && "
        detailed += f"{self._conda_exe} update -c mantid/label/{suffix} mantidimaging"
        return msg, detailed

    def _retrieve_conda_installed_version(self) -> None:
        query_result = subprocess.check_output(f"{self._conda_exe} list mantidimaging", shell=True,
                                               env=os.environ).decode("utf-8").strip()
        local_packages = [line.split() for line in query_result.splitlines() if not line.startswith('#')]

        if not local_packages:
            LOG.info("Running a development build without a local Mantid Imaging package installation.")
            # no local installation, no point sending out API requests
            # just returns as "unstable" label
            self._conda_installed_version = ""
            self._conda_installed_label = "unstable"
            return

        local_package = local_packages[-1]
        self._conda_installed_version = local_package[1]
        self._conda_installed_label = local_package[3].rpartition("/")[2]

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

        if self.get_conda_installed_label() == "main":
            self._conda_available_version = remote_main_version
        else:
            self._conda_available_version = remote_unstable_version


versions = CheckVersion()


def _parse_version(package_version_string: Optional[str]) -> version.Version:
    if package_version_string is None:
        raise ValueError

    normalised_version_string = package_version_string.replace("_", ".post")
    return version.parse(normalised_version_string)


def _version_is_uptodate(local: version.Version, remote: version.Version):
    return local >= remote
