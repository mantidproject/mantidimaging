#!/usr/bin/env python
# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later

# Check the release note format if a new release note is added or modified.

from __future__ import annotations
from pathlib import Path
import re
import requests
import subprocess

RELEASE_NOTES_DIR: Path = Path("docs/release_notes/next")
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

    def get_all_issue_numbers(self) -> set[str]:
        """
        Returns a set of all issue numbers found in the filename and content.
        """
        numbers = set()
        match = self.FILENAME_PATTERN.match(self.name)
        if match:
            numbers.add(match.group(2))
        if self.content is None:
            self.load_content()
        match_content = self.CONTENT_PATTERN.search(self.content or "")
        if match_content:
            numbers.add(match_content.group(1))
        return numbers


class FindStagedReleaseNotes:
    """
    Find staged release notes in a given target directory.
    """
    
    def __init__(self, target_directory: Path) -> None:
        self.target_directory: Path = target_directory

    def get_staged_files(self) -> list[Path]:
        """
        Returns a list of file paths that are staged for commit from the target directory.
        """
        result = subprocess.run(["git", "diff", "--cached", "--name-only", "--diff-filter=ACM"],
                                stdout=subprocess.PIPE,
                                encoding="utf-8")
        # Convert staged files to a list of path objects, then filter by target directory
        stage_files = [Path(file.strip()) for file in result.stdout.splitlines()]
        release_notes = [
            file for file in stage_files
            if self.target_directory in file.parents or file.parent == self.target_directory
        ]
        return release_notes


class GitHubIssueChecker:
    """
    Checks if a GitHub issue or PR exists.
    """

    def __init__(self, repo_url: str) -> None:
        self.repo_url = repo_url
        self.network_available = False
        self._check_network_availability()

    def _check_network_availability(self) -> None:
        """
        Set nework availability based on connectivity to the GitHub repository.
        """
        try:
            response = requests.get("https://github.com", timeout=5)
            self.network_available = response.status_code == 200
        except requests.RequestException:
            self.network_available = False
            print("Warning: Network unavailable, skipping GitHub issue existence checks for all files.")

    def check_issue_exists(self, issue_number: str) -> bool:
        """
        Check if a GitHub issu or PR exists based on a given issue number.
        """
        if not self.network_available:
            return False
        url_issue = f"{self.repo_url}/issues/{issue_number}"
        try:
            response = requests.get(url_issue, timeout=5)
            return response.status_code == 200
        except requests.RequestException as response_error:
            print(f"Error checking issue {issue_number}: {response_error}")
            return False


class ReleaseNoteDirectory:
    """
    Manages a directory of release notes, providing methods to list files and check for issue numbers.
    """

    def __init__(self, directory: Path) -> None:
        self.directory: Path = directory

    def list_files(self, exclude_files: list[Path] = None) -> list[ReleaseNote]:
        """
        List all release note files in the directory.
        """
        exclude_set = {file.resolve() for file in exclude_files} if exclude_files else set()
        return [
            ReleaseNote(file) for file in self.directory.iterdir()
            if file.is_file() and file.resolve() not in exclude_set
        ]

    def get_issue_numbers(self, exclude_files: list[Path]) -> set[str]:
        """
        Return a set of all issue numbers found in filenames and file contents in the release notes directory.
        """
        issue_numbers = set()
        for release_note in self.list_files(exclude_files):
            issue_numbers.update(release_note.get_all_issue_numbers())
        return issue_numbers


class ReleaseNoteValidator:
    """
    Centralise all validation logic to check the format of release notes.
    """

    def __init__(self, release_notes_dir: Path, repo_url: str) -> None:
        self.release_notes_dir = ReleaseNoteDirectory(release_notes_dir)
        self.issue_checker = GitHubIssueChecker(repo_url)
        self.warnings_found = False

    def _warn_duplicates(self, issue_number: str, note: ReleaseNote, existing_issue_numbers: set[str]) -> None:
        """Check for duplicate issue numbers in the filename and file content"""
        if issue_number and issue_number in existing_issue_numbers:
            print(f"Warning: Issue number '{issue_number}' in {note.name} is a duplicate of an existing "
                  f"issue number in the same directory.")
            self.warnings_found = True

    def _warn_github_issue_not_found(self, issue_number: str, note: ReleaseNote) -> None:
        """Check for GitHub issue existence"""
        if issue_number and not self.issue_checker.check_issue_exists(issue_number):
            print(f"Warning: Issue number '{issue_number}' in {note.name} does not exist on GitHub.")
            self.warnings_found = True

    def validate(self, staged_files: list[Path]) -> None:
        existing_issue_numbers = self.release_notes_dir.get_issue_numbers(exclude_files=staged_files)

        for file in staged_files:
            release_note = ReleaseNote(file)
            valid_filename = release_note.validate_filename()

            if not valid_filename:
                match = ReleaseNote.CONTENT_PATTERN.search(release_note.content or "")
                if match:
                    content_issue_number = match.group(1)
                    print(f"Warning: Filename '{release_note.name}' is missing a valid issue number, "
                          f"but content has the issue number '{content_issue_number}'.")
                self.warnings_found = True
                continue

            valid_content = release_note.validate_content()
            for issue_number in release_note.get_all_issue_numbers():
                self._warn_duplicates(issue_number, release_note, existing_issue_numbers)
            if not valid_content:
                self.warnings_found = True
                continue
            self._warn_github_issue_not_found(release_note.issue_number, release_note)


def main() -> None:
    staged_files = FindStagedReleaseNotes(RELEASE_NOTES_DIR).get_staged_files()
    if not staged_files:
        print("No staged release notes found.")
        return
    validator = ReleaseNoteValidator(RELEASE_NOTES_DIR, REPO_URL)
    validator.validate(staged_files)

    if validator.warnings_found:
        exit(1)
    exit(0)


if __name__ == "__main__":
    main()
