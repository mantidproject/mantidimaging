#!/usr/bin/env python
# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later

# Check the release note format if a new release note is added or modified.

from __future__ import annotations
from pathlib import Path

import subprocess

RELEASE_NOTES_DIR = "docs/release_notes/next"
REPO_URL = "https://github.com/mantidproject/mantidimaging"


class FindStagedReleaseNotes:
    """
    Find staged release notes in a given target directory.
    """

    def __init__(self, target_directory: str) -> None:
        self.target_directory = target_directory

    def get_staged_files(self) -> list[str]:
        """
        Returns a list of file paths that are staged for commit from the target directory.
        """
        result = subprocess.run(["git", "diff", "--cached", "--name-only", "--diff-filter=ACM"],
                                stdout=subprocess.PIPE,
                                encoding="utf-8")
        # Convert staged files to a list of path objects, then filter by target directory
        stage_files = [Path(file.strip()) for file in result.stdout.splitlines()]
        release_notes = [
            str(file) for file in stage_files
            if self.target_directory in file.parents or file.parent == Path(self.target_directory)
        ]
        return release_notes


def main() -> None:
    staged_files = FindStagedReleaseNotes(RELEASE_NOTES_DIR).get_staged_files()
    if not staged_files:
        print("No staged release notes found.")
        return


if __name__ == "__main__":
    main()
