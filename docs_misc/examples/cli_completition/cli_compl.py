#!/usr/bin/env python
# PYTHON_ARGCOMPLETE_OK

import argparse as ap

import argcomplete
from argcomplete.completers import ChoicesCompleter, EnvironCompleter


def main(**args):
    pass


if __name__ == '__main__':
    print("im parsing3")
    parser = ap.ArgumentParser()
    parser.add_argument(
        '--positional', choices=['spam', 'eggs']).completer = EnvironCompleter

    parser.add_argument(
        '--optional',
        choices=['foo1', 'foo2', 'bar']).completer = EnvironCompleter
    parser.add_argument(
        "--protocol", choices=('http', 'https', 'ssh', 'rsync', 'wss'))
    parser.add_argument("--proto").completer = ChoicesCompleter(
        ('http', 'https', 'ssh', 'rsync', 'wss'))
    argcomplete.autocomplete(parser)
    args = parser.parse_args()
    main(**vars(args))
