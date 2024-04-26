# Copyright (C) 2024 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

from pathlib import Path
import re
from typing import Final
from collections.abc import Iterator
from logging import getLogger

from mantidimaging.core.utility.data_containers import FILE_TYPES

LOG = getLogger(__name__)

IMAGE_FORMAT_EXTENSIONS: Final = ['fits', 'fit', 'tif', 'tiff']


class FilenamePattern:
    """
    Representation of a filename pattern to handle stacks of related images

    Handles patterns like "aaaa_####.bbb" where # are digits
    """
    PATTERN_p = r'^(.+?)'
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
            self.re_pattern = re.compile("^" + re.escape(prefix) + "(([1-9][0-9]*)?[0-9]{" + str(digit_count) + "})" +
                                         re.escape(suffix) + "$")

        self.re_pattern_metadata = re.compile("^" + re.escape(prefix.rstrip("_ ")) + ".json$")
        self.template = prefix + "{:0" + str(digit_count) + "d}" + suffix

    @classmethod
    def from_name(cls, filename: str) -> FilenamePattern:
        result = cls.PATTERN.search(filename)

        if result is None:
            if "." in filename:
                name, _, ext = filename.rpartition(".")
                return cls(name, 0, "." + ext)
            else:
                return cls(filename, 0, "")

        prefix = result.group(1)
        digits = result.group(2)
        ext = result.group(3)
        return cls(prefix, len(digits), ext)

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


class FilenamePatternGolden(FilenamePattern):
    """
    Representation of a filename pattern for IMAT Golden ratio scans

    "aaaa_**.**_####.bbb" where **.** is an angle and #### is the projection number
    """
    PATTERN_p = r'^(.+?)'
    PATTERN_a = r'_([0-9\.]+)_'
    PATTERN_d = r'([0-9]+)'
    PATTERN_s = r'(\.[a-zA-Z]+)$'
    PATTERN = re.compile(PATTERN_p + PATTERN_a + PATTERN_d + PATTERN_s)

    def __init__(self, prefix: str, digit_count: int, suffix: str):
        self.prefix = prefix
        self.digit_count = digit_count
        self.suffix = suffix
        self.name_store: dict[int, str] = {}

        self.re_pattern = re.compile("^" + re.escape(prefix) + self.PATTERN_a + "(([1-9][0-9]*)?[0-9]{" +
                                     str(digit_count) + "})" + re.escape(suffix) + "$")

        self.re_pattern_metadata = re.compile("^" + re.escape(prefix.rstrip("_ ")) + ".json$")

    @classmethod
    def from_name(cls, filename: str) -> FilenamePattern:
        result = cls.PATTERN.search(filename)
        if result is None:
            raise ValueError(f"Could not match FilenamePatternGolden from: '{filename}'")

        prefix = result.group(1)
        digits = result.group(3)
        ext = result.group(4)
        return cls(prefix, len(digits), ext)

    def get_index(self, filename: str) -> int:
        result = self.re_pattern.match(filename)
        if result is None:
            raise ValueError(f"Filename ({filename}) does not match pattern: {self.re_pattern}")
        index = int(result.group(2))
        self.name_store[index] = filename
        return index

    def generate(self, index: int) -> str:
        return self.name_store[index]


class FilenameGroup:

    def __init__(self, directory: Path, pattern: FilenamePattern, all_indexes: list[int]):
        self.directory = directory
        self.pattern = pattern
        self.all_indexes = all_indexes
        self.metadata_path: Path | None = None
        self.log_path: Path | None = None
        self.shutter_count_path: Path | None = None

    @classmethod
    def from_file(cls, path: Path | str) -> FilenameGroup:
        path = Path(path)
        if path.is_dir():
            raise ValueError(f"path is a directory: {path}")
        if 'WindowsPath' in type(path).__name__:
            # for a windows like path, resolve actual case
            path = path.resolve()
        pattern_class = cls.get_pattern_class(path)
        directory = path.parent
        name = path.name
        pattern = pattern_class.from_name(name)
        index = pattern.get_index(name)
        new_filename_group = cls(directory, pattern, [index])

        return new_filename_group

    @classmethod
    def from_directory(cls, path: Path | str) -> FilenameGroup | None:
        path = Path(path)
        if not path.is_dir():
            raise ValueError(f"path is a file: {path}")

        files = (f for f in path.iterdir() if cls.valid_image_filename(f))

        try:
            first_file = min(files)
        except ValueError:
            return None
        return cls.from_file(first_file)

    @staticmethod
    def valid_image_filename(f: Path) -> bool:
        """
        Check that file is not hidden (starts with a dot) and that it has an image extension
        """
        return f.name[0] != '.' and f.suffix[1:] in IMAGE_FORMAT_EXTENSIONS

    @classmethod
    def get_pattern_class(cls, path):
        if 'grtomo' in path.name.lower():
            return FilenamePatternGolden
        else:
            return FilenamePattern

    def all_files(self) -> Iterator[Path]:
        for index in self.all_indexes:
            yield self.directory / self.pattern.generate(index)

    def first_file(self):
        return next(self.all_files())

    def find_all_files(self) -> None:
        self.all_indexes = []
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

    def find_shutter_count_file(self) -> None:
        """
        Find the shutter count file in directory if it exists. The file must be in the parent directory.
        """
        shutter_count_pattern = self.directory.name + "*" + "ShutterCount" + ".txt"
        shutter_count_paths = list(self.directory.parent.glob(shutter_count_pattern))
        if shutter_count_paths:
            shortest = min(shutter_count_paths, key=lambda p: len(p.name))
            self.shutter_count_path = self.directory / shortest

    def find_related(self, file_type: FILE_TYPES) -> FilenameGroup | None:
        if self.directory.name not in ["Tomo", "tomo"]:
            return None

        if file_type == FILE_TYPES.PROJ_180:
            return self._find_related_180_proj()

        test_names = [file_type.fname.replace(" ", "_")]
        if file_type.suffix == "Before":
            test_names.append(file_type.tname)
        test_names.extend([s.lower() for s in test_names])

        for test_name in test_names:
            new_dir = self.directory.parent / test_name
            if new_dir.exists():
                fg = self.from_directory(new_dir)
                if fg is not None:
                    return fg

        return None

    def _find_related_180_proj(self) -> FilenameGroup | None:
        sample_first_name = self.first_file().name

        test_name = "180deg"

        new_dir = self.directory.parent / test_name
        if new_dir.exists():
            for trim_numbers in [True, False]:
                if trim_numbers:
                    new_name = re.sub(r'_([0-9]+)', "", sample_first_name)
                else:
                    new_name = sample_first_name
                new_name = new_name.replace("Tomo", test_name).replace("tomo", test_name)
                new_path = new_dir / new_name
                if new_path.exists():
                    return self.from_file(new_path)

        return None
