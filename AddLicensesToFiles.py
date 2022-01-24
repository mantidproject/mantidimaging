#!/usr/bin/env python
# Copyright (C) 2022 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later

# Update license comment block at the top files
#
# Reads the license and file glob pattern from .licenserc.json. It will
# update any file that does not match. It will remove any old license lines,
# identified by being leading comments containing "Copyright" or "License".

import glob
import json

update_count = 0


def update_copyrights_glob(globpattern, copyright_string):
    for filepath in glob.iglob(globpattern, recursive=True):
        update_copyright_file(filepath, copyright_string)


def update_copyright_file(filepath, copyright_string):
    global update_count
    copyright_lines = copyright_string.split("\n")
    lines = open(filepath).readlines()
    if lines[0].startswith("#!"):
        shebang_line = lines.pop(0)
    else:
        shebang_line = ""

    # Check if the copyright is already correct
    is_good = True
    for i in range(len(copyright_lines)):
        if lines[i].strip() != copyright_lines[i].strip():
            is_good = False
    if is_good:
        return

    # Remove any existing copyright lines
    while len(lines):
        if ((lines[0].startswith("#") and "Copyright" in lines[0])
                or (lines[0].startswith("#") and "License" in lines[0])):
            lines.pop(0)
        else:
            break

    # Output modified file
    update_count += 1
    with open(filepath, "w") as outfile:
        if shebang_line:
            outfile.write(shebang_line)
        outfile.write("\n".join(copyright_lines) + "\n")

        outfile.write("".join(lines))


if __name__ == "__main__":
    copyright_strings = json.load(open(".licenserc.json"))

    for globpattern, copyright_string in copyright_strings.items():
        update_copyrights_glob(globpattern, copyright_string)

    print("Updated", update_count, "files")
