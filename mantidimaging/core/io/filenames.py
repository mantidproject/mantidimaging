# Copyright (C) 2023 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

from pathlib import Path
import re
from typing import List, Iterator, Optional, Union
from logging import getLogger

LOG = getLogger(__name__)


class FilenamePattern:
    """
    Representation of a filename pattern to handle stacks of related images

    Handles patterns like "aaaa_####.bbb" where # are digits
    """
    PATTERN_p = r'^([a-zA-Z0-9_]+?)'
    PATTERN_d = r'([0-9]+)'
    PATTERN_s = r'(\.[a-zA-Z_]+)$'
    PATTERN = re.compile(PATTERN_p + PATTERN_d + PATTERN_s)

    def __init__(self, prefix: str, digit_count: int, suffix: str):
        self.prefix = prefix
        self.digit_count = digit_count
        self.suffix = suffix

        if digit_count == 0:
            self.re_pattern = re.compile("^" + re.escape(prefix) + re.escape(suffix) + "$")
        else:
            # Note: allow extra leading digits, for data sets that go 001 ... 998, 999, 1000, 1001
            self.re_pattern = re.compile("^" + re.escape(prefix) + "([1-9]?[0-9]{" + str(digit_count) + "})" +
                                         re.escape(suffix) + "$")

        self.re_pattern_metadata = re.compile("^" + re.escape(prefix.rstrip("_ ")) + ".json$")
        self.template = prefix + "{:0" + str(digit_count) + "d}" + suffix

    @classmethod
    def from_name(cls, filename: str) -> "FilenamePattern":
        result = FilenamePattern.PATTERN.search(filename)

        if result is None:
            if "." in filename:
                name, _, ext = filename.rpartition(".")
                return FilenamePattern(name, 0, "." + ext)
            else:
                return FilenamePattern(filename, 0, "")

        prefix = result.group(1)
        digits = result.group(2)
        ext = result.group(3)

        return FilenamePattern(prefix, len(digits), ext)

    def generate(self, index: int) -> str:
        if self.digit_count == 0:
            return self.prefix + self.suffix
        return self.template.format(index)

    def match(self, filename: str) -> bool:
        return self.re_pattern.match(filename) is not None

    def get_index(self, filename: str) -> int:
        result = self.re_pattern.match(filename)
        if result is None:
            raise ValueError(f"Filename ({filename}) does not match pattern: {self.re_pattern}")
        if self.digit_count == 0:
            return 0
        return int(result.group(1))

    def match_metadata(self, filename: str) -> bool:
        return self.re_pattern_metadata.match(filename) is not None


class FilenameGroup:
    def __init__(self, directory: Path, pattern: FilenamePattern, all_indexes: List[int]):
        self.directory = directory
        self.pattern = pattern
        self.all_indexes = all_indexes
        self.metadata_path: Optional[Path] = None
        self.log_path: Optional[Path] = None

    @classmethod
    def from_file(cls, path: Union[Path, str]) -> "FilenameGroup":
        path = Path(path)
        if path.is_dir():
            raise ValueError(f"path is a directory: {path}")
        directory = path.parent
        name = path.name
        pattern = FilenamePattern.from_name(name)
        index = pattern.get_index(name)
        new_filename_group = cls(directory, pattern, [index])

        return new_filename_group

    def all_files(self) -> Iterator[Path]:
        for index in self.all_indexes:
            yield self.directory / self.pattern.generate(index)

    def find_all_files(self) -> None:
        for filename in self.directory.iterdir():
            if self.pattern.match(filename.name):
                self.all_indexes.append(self.pattern.get_index(filename.name))

            if self.pattern.match_metadata(filename.name):
                if self.metadata_path is not None:
                    LOG.warning(f"Multiple metadata files found: {filename}")
                self.metadata_path = filename
        self.all_indexes.sort()

    def find_log_file(self) -> None:
        parent_directory = self.directory.parent
        log_pattern = self.directory.name + "*" + ".txt"
        log_paths = list(parent_directory.glob(log_pattern))

        if log_paths:
            # choose shortest match
            shortest = min(log_paths, key=lambda p: len(p.name))
            self.log_path = self.directory / shortest
