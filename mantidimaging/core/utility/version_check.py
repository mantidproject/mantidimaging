# Copyright (C) 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later

import json
import os
import subprocess
from logging import getLogger
from typing import Callable
from collections import namedtuple

import requests

LOG = getLogger(__name__)
ParsedVersion = namedtuple('ParsedVersion', ['version', 'commits'])


def check_version_and_label(action: Callable[[str], None]) -> bool:
    """
    Checks the package version and label. Shows a warning message to user
    and an update command if the version is out of date for the current package's label.

    Supports labels: main and unstable

    :returns: Whether the label is "unstable" (False) or "main" (True)
    """
    LOG.info("Finding and comparing mantidimaging versions")
    local_package = subprocess.check_output("conda list mantidimaging | grep '^[^#]' | awk 'END{print $2,$4}'",
                                            shell=True,
                                            env=os.environ).decode("utf-8").strip()

    if local_package == "":
        LOG.info("Running a development build without a local Mantid Imaging package installation.")
        # no local installation, no point sending out API requests
        # just returns as "unstable" label
        return False

    local_version, local_label = local_package.split()
    # makes sure this is no longer used by accident
    del local_package

    # if the label contains "main", it will return True
    # if it doesn't then it will return False and mark
    # the app as unstable
    is_main_label = "unstable" not in local_label

    try:
        response = requests.get("https://api.anaconda.org/package/mantid/mantidimaging")
        remote_main_version = json.loads(response.content)["latest_version"]
        remote_unstable_version = json.loads(
            response.content)["versions"][-1] if len(json.loads(response.content)["versions"]) > 0 else ''
    except Exception:
        # if anything goes wrong, in the end we don't have the version
        LOG.info("Could not connect to Anaconda remote to retrieve the latest version")
        return is_main_label

    parsed_local_version = _parse_version(local_version)
    del local_version

    if is_main_label:
        parsed_remote_version = _parse_version(remote_main_version)
    else:
        parsed_remote_version = _parse_version(remote_unstable_version)

    _do_version_check(parsed_local_version, parsed_remote_version, action, is_main_label)
    return is_main_label


def _parse_version(package_version_string: str) -> ParsedVersion:
    local_version, local_commits_since_last = package_version_string.split("_")
    return ParsedVersion(tuple(map(int, local_version.split("."))), int(local_commits_since_last))


def _do_version_check(local: ParsedVersion, remote: ParsedVersion, action: Callable[[str], None], is_main_label: bool):
    if local.version < remote.version or local.commits < remote.commits:
        # no suffix if main, else adds Unstable
        suffix = "" if is_main_label else " Unstable"

        msg = f"Not running the latest Mantid Imaging{suffix}. Found version {_make_version_str(local)}, " \
              f"latest: {_make_version_str(remote)}. Please check the terminal for an update command!"
        LOG.info(msg)

        # for unstable packages these run variables are prepended to the command
        # for main packages nothing is prepended, and the script's defaults are used
        command_prefix = "" if is_main_label else "ENVIRONMENT_NAME=mantidimaging_unstable REPO_LABEL=unstable "

        LOG.info("To update your environment please copy and run the following command:\n\n"
                 "source /opt/miniconda/bin/activate /opt/miniconda && "
                 f"{command_prefix}source "
                 "<(curl -s https://raw.githubusercontent.com/mantidproject/mantidimaging/master/install.sh)")
        action(msg)
    else:
        LOG.info("Running the latest Mantid Imaging")


def _make_version_str(parsed: ParsedVersion) -> str:
    return f"{'.'.join([str(v) for v in parsed.version])}_{parsed.commits}"
