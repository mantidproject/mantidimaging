#!/usr/bin/env python
# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later

# Check the release note format if a new release note is added or modified.

from __future__ import annotations
from pathlib import Path
import re

import subprocess

RELEASE_NOTES_DIR = "docs/release_notes/next"
REPO_URL = "https://github.com/mantidproject/mantidimaging"


class ReleaseNote:
    """
    Represents a release note file with its properties and validation methods.
    """
    FILENAME_PATTERN = re.compile(r"^(fix|dev|feature)-(\d+)-.+$")  # Matches "fix-1234-some-feature
    CONTENT_PATTERN = re.compile(r"#(\d+):\s+.+")  # Matches "#1234: Some description"

    def __init__(self, filepath: Path) -> None:
        self.filepath = filepath
        self.name = filepath.name
        self.prefix = None
        self.issue_number = None
        self.content_issue_number = None
        self.content = None

    def validate_filename(self) -> bool:
        match = self.FILENAME_PATTERN.match(self.name)
        if not match:
            print(f"Warning: Filename '{self.name}' is invalid.\n"
                  "  Expected format: <fix|dev|feature>-<issue_number>-<description>\n"
                  "  Example: dev-2769-release_notes_pre-commit")
            return False
        self.prefix, self.issue_number = match.group(1), match.group(2)
        return True

    def load_content(self) -> None:
        try:
            self.content = self.filepath.read_text(encoding='utf-8').strip()
        except (FileNotFoundError, UnicodeDecodeError) as file_error:
            print(f"Error reading {self.filepath}: {file_error}")
            self.content = None

    def validate_content(self) -> bool:
        """
        Validate that the content of the release note matches the issue number in the filename
        and the content pattern matches the expected format i.e. "#1234: Some description".
        """
        if self.content is None:
            self.load_content()
        if self.content is None:
            print(f"Warning: No content loaded for {self.filepath}.")
            return False

        match = self.CONTENT_PATTERN.search(self.content)
        if not match:
            print(f"Warning: Content in {self.name} does not match required pattern '#<issue_number>: <description>'.")
            return False

        self.content_issue_number = match.group(1)
        if self.content_issue_number != self.issue_number:
            print(f"Warning: Issue number in content '{self.content_issue_number}' "
                  f"does not match filename '{self.issue_number}' in {self.name}.")
            return False

        return True


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
    print(f"Staged release notes found: {len(staged_files)}")
    release_notes = [ReleaseNote(Path(file)) for file in staged_files]
    for note in release_notes:
        print(f"Validating release note: {note.name}")
        note.validate_filename()
        note.validate_content()
        print("\n")


if __name__ == "__main__":
    main()
