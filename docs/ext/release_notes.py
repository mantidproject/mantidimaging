# Copyright (C) 2024 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

from pathlib import Path
from typing import Iterable

from docutils import nodes
from docutils.statemachine import StringList
from docutils.parsers.rst import Directive
from sphinx.errors import SphinxError
from sphinx.util.nodes import nested_parse_with_titles
"""Custom extension to collect release notes from separate files

Use one of:
.. release_notes:: feature
.. release_notes:: fix
.. release_notes:: dev

"""


class ReleaseNotes(Directive):
    has_content = True

    @classmethod
    def make_rst(cls, note_type: str) -> StringList:
        note_paths: Iterable[Path] = (Path() / 'docs' / 'release_notes' / 'next').glob(note_type + '*')

        rst = StringList()
        try:
            note_paths = sorted(note_paths, key=lambda p: int(p.name.split('-')[1]))
        except ValueError as exc:
            raise cls.severe('Could not sort release notes, check filenames.') from exc

        for n, note_path in enumerate(note_paths):
            note_content = note_path.read_text().strip().split('\n')
            if len(note_content) != 1:
                raise cls.severe(f'Release note file should have 1 line: {note_path}.')

            rst.append(f"- {note_content[0]}", "generated.rst", n)

        return rst

    def run(self) -> list[nodes.Node]:
        if len(self.content) != 1:
            raise self.severe('Directive release_notes needs a value.')
        if not self.content[0].isalnum():
            raise self.severe(f'Value should be single word. Got "{self.content[0]}".')

        note_type = self.content[0]
        rst = self.make_rst(note_type)

        node = nodes.section()
        node.document = self.state.document
        nested_parse_with_titles(self.state, rst, node)

        return node.children

    @staticmethod
    def severe(message):
        """Override with an error strong enough to stop build"""
        return SphinxError(f'ReleaseNotes: {message}')


def setup(app):
    app.add_directive("release_notes", ReleaseNotes)

    return {
        'version': '0.1',
        'parallel_read_safe': True,
        'parallel_write_safe': True,
    }
