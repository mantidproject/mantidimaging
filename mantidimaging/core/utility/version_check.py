# Copyright (C) 2023 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

import json
import os
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
    _version: str
    _package_type: str
    _conda_available_version: Optional[str]

    def __init__(self):
        self._version = package_version
        self._package_type = package_type
        self._conda_available_version = None

    def _retrieve_versions(self) -> None:
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
        print(f"Install method {self._package_type}")
        if self._package_type == "conda":
            print(f"conda_available_version {self.get_conda_available_version()}")
        if git_hash:
            print(f"Git hash {git_hash}")

    def get_version(self) -> str:
        """Get built in version"""
        return self._version

    def is_prerelease(self) -> bool:
        return version.Version(self.get_version()).is_prerelease

    def get_conda_available_version(self) -> str:
        """Get latest version number from conda"""
        if self._conda_available_version is None:
            self._retrieve_conda_available_version()
        assert self._conda_available_version is not None
        return self._conda_available_version

    def needs_update(self) -> bool:
        if self._package_type == "conda" and not self.is_conda_uptodate():
            return True
        return False

    def is_conda_uptodate(self) -> bool:
        """Check if up to date with lasted version in conda"""
        if self.get_conda_available_version() == "":
            # If unable to get conda versions then assume everything is good
            return True

        return _version_is_uptodate(self.get_version(), self.get_conda_available_version())

    def conda_update_message(self) -> tuple:
        conda_exe = self.find_conda_executable()
        suffix = "unstable" if self.is_prerelease() else "main"

        msg = "Not running the latest Mantid Imaging"
        if suffix != "main":
            msg += f"-{suffix}"
        msg += f".\nFound version {self.get_version()}, "
        msg += f"latest: {self.get_conda_available_version()}.\nPlease check the terminal for an update command!"

        detailed = f"Not running the latest Mantid Imaging {suffix}.\n"
        detailed += f"Found version {self.get_version()}, "
        detailed += f"latest: {self.get_conda_available_version()}.\n"
        detailed += "To update your environment please copy and run the following command:\n"
        if sys.platform == 'linux':
            detailed += f"{conda_exe} activate {os.environ['CONDA_PREFIX']} && "
        detailed += f"{conda_exe} update -c mantid/label/{suffix} mantidimaging"
        return msg, detailed

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

        if self.is_prerelease():
            self._conda_available_version = remote_unstable_version
        else:
            self._conda_available_version = remote_main_version


versions = CheckVersion()


def _parse_version(package_version_string: str) -> version.Version:
    normalised_version_string = package_version_string.replace("_", ".post")
    return version.parse(normalised_version_string)


def _version_is_uptodate(local: str, remote: str):
    return _parse_version(local) >= _parse_version(remote)
