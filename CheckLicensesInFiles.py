#!/usr/bin/env python
# Copyright (C) 2023 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

# Checks the license comment block at the top of files
#
# Reads the license content from .licenserc.json and checks if the files passed in as arguments have matching
# license lines. Written primarily for use as a pre-commit check, so the pre-commit configuration limits the check to
# only Python files and the passed in arguments will be the files staged for commit.

import json
import sys
from typing import List, Dict


def load_copyright_header() -> Dict[str, str]:
    return json.load(open(".licenserc.json"))


def find_files_with_incorrect_license_headers(filepaths: List[str], copyright_text: str) -> List[str]:
    copyright_lines = copyright_text.split("\n")
    incorrect_files = []

    for filepath in filepaths:
        lines = open(filepath).readlines()

        if len(lines) > 0:
            if has_shebang_line(lines):
                del lines[0]

            if not has_correct_copyright_lines(lines, copyright_lines):
                incorrect_files.append(filepath)

    return incorrect_files


def has_shebang_line(file_lines: List[str]) -> bool:
    return file_lines[0].startswith("#!")


def has_correct_copyright_lines(file_lines: List[str], copyright_lines: List[str]) -> bool:
    if len(file_lines) < len(copyright_lines):
        return False

    for i in range(len(copyright_lines)):
        if file_lines[i].strip() != copyright_lines[i].strip():
            return False
    return True


if __name__ == "__main__":
    copyright_strings = load_copyright_header()
    files_to_check = sys.argv[1:]

    files_in_error = set()
    for copyright_string in copyright_strings.values():
        files_in_error.update(find_files_with_incorrect_license_headers(files_to_check, copyright_string))

    if len(files_in_error) > 0:
        print('The following files contain errors in their licenses:\n')
        print('\n'.join(files_in_error))
        exit(1)
    else:
        print("All files have correct licenses")

    exit(0)
