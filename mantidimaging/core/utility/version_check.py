from logging import getLogger
from typing import Tuple

LOG = getLogger(__name__)


def find_if_latest_version():
    """[ "`conda list | grep mantidimaging | awk 'END{print $2}'`" = "`conda search -c dtasev mantidimaging | awk 'END{print $2}'`" ]"""
    LOG.info("Finding and comparing mantidimaging versions")
    import subprocess
    import os
    local_mantid_package = subprocess.check_output(
        "conda list | grep mantidimaging | awk 'END{print $2}'", shell=True, env=os.environ).decode("utf-8").strip()
    remote_mantid_package = subprocess.check_output(
        "conda search -c dtasev mantidimaging | awk 'END{print $2}'", shell=True, env=os.environ).decode(
        "utf-8").strip()
    if local_mantid_package == "":
        LOG.info("Running a development build without a local mantidimaging package installation.")
    else:
        local_version, local_commits_since_last = _parse_version(local_mantid_package)
        remote_version, remote_commits_since_last = _parse_version(remote_mantid_package)

        if local_version < remote_version or local_commits_since_last < remote_commits_since_last:
            LOG.info(
                f"Not running the latest mantidimaging. Found {local_mantid_package}, latest: {remote_mantid_package}")
            return
        LOG.info("Running the latest mantidimaging")


def _parse_version(package_version_string: str) -> Tuple[Tuple[int, ...], int]:
    local_version, local_commits_since_last = package_version_string.split("_")
    return tuple(map(int, local_version.split("."))), int(local_commits_since_last)
