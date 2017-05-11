from __future__ import absolute_import, division, print_function

from timeit import timeit


def multiple(files):
    # specify the checks to remove specific files
    checks = [
        lambda x: '.py' in x,  # removes all files that DON'T have .py in the name
        lambda x: '.pyc' not in x,  # removes all files that DO have .pyc in the name
        lambda x: '__init__' not in x,  # removes all files that DO have __init__ in the name
        lambda x: 'cli_registrator.py' not in x  # removes all files that have this module's name in the name
    ]

    for check in checks:
        files = filter(check, files)


def single(files):
    files = filter(
        lambda filename: '.py' in filename and '.pyc' not in filename and '__init__' not in filename and 'cli_registrator.py' not in filename,
        files)


if __name__ == '__main__':
    files = [
        "some_file.pyc", "some_other_file.py", "what_the_fuck_are_you.md",
        "__init__.py"
    ] * 100

    print("Timing in a single statement", timeit(
        "multiple(files)",
        "from __main__ import files, multiple",
        number=100000))

    print("Timing with separate statements", timeit(
        "single(files)", "from __main__ import files, single", number=100000))
