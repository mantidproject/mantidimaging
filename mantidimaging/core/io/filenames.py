# Copyright (C) 2022 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later

import re


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

        self.re_pattern = re.compile("^" + re.escape(prefix) + "([0-9]{" + str(digit_count) + "})" + re.escape(suffix) +
                                     "$")
        self.template = prefix + "{:0" + str(digit_count) + "d}" + suffix

    @classmethod
    def from_name(cls, filename: str) -> "FilenamePattern":
        result = FilenamePattern.PATTERN.search(filename)

        if result is None:
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

    def get_value(self, filename: str) -> int:
        result = self.re_pattern.match(filename)
        if result is None:
            raise ValueError(f"Filename ({filename}) does not match pattern: {self.re_pattern}")
        if self.digit_count == 0:
            return 0
        return int(result.group(1))
