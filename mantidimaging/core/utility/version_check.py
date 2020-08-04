import json
import os
import subprocess
from logging import getLogger
from typing import Tuple, Callable

import requests

LOG = getLogger(__name__)


def find_if_latest_version(action: Callable[[str], None]):
    LOG.info("Finding and comparing mantidimaging versions")
    local_mantid_package = subprocess.check_output("conda list | grep mantidimaging | awk 'END{print $2}'",
                                                   shell=True,
                                                   env=os.environ).decode("utf-8").strip()
    try:
        response = requests.get("https://api.anaconda.org/package/dtasev/mantidimaging")
        remote_mantid_package = json.loads(response.content)["latest_version"]
    except Exception:
        # whatever goes wrong, in the end we don't have the version
        remote_mantid_package = ''
    if local_mantid_package == "":
        LOG.info("Running a development build without a local Mantid Imaging package installation.")
    elif remote_mantid_package == "":
        LOG.info("Could not connect Anaconda remote to get the latest version")
    else:
        local_version, local_commits_since_last = _parse_version(local_mantid_package)
        remote_version, remote_commits_since_last = _parse_version(remote_mantid_package)

        if local_version < remote_version or local_commits_since_last < remote_commits_since_last:
            msg = f"Not running the latest Mantid Imaging. Found {local_mantid_package}, " \
                  f"latest: {remote_mantid_package}"
            LOG.info(msg)
            action(msg)
            return
        LOG.info("Running the latest Mantid Imaging")


def _parse_version(package_version_string: str) -> Tuple[Tuple[int, ...], int]:
    local_version, local_commits_since_last = package_version_string.split("_")
    return tuple(map(int, local_version.split("."))), int(local_commits_since_last)
