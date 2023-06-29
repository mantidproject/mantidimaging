# Copyright (C) 2023 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

from typing import List
import inspect

from docutils import nodes
from docutils.nodes import Node
from docutils.statemachine import ViewList
from docutils.parsers.rst import Directive
from sphinx.util.nodes import nested_parse_with_titles
"""Custom extension to add nicely formatted documentation for the operations.

Use:
.. operations_user_doc::

in a documentation rst file to generate.
"""


def make_heading(s: str, char: str) -> List[str]:
    return [s, len(s) * char, ""]


def split_lines(s: str) -> List[str]:
    s = s.replace("\n\n", "DOUBLE_NEW_LINE")
    s = s.replace("\n", " ")
    s = s.replace("DOUBLE_NEW_LINE", "\n\n")
    return s.split("\n")


PARAM_SKIP_LIST = ["images", "progress"]


def get_params(s: str) -> List[str]:
    ret = []
    for line in s.split("\n"):
        if line.strip().startswith(":param"):
            param_name = line.strip().split()[1].strip(':')
            if param_name in PARAM_SKIP_LIST:
                continue
            ret.append(line.strip())
        elif line.strip().startswith(":return"):
            pass
        elif line.strip() and ret:
            ret[-1] = ret[-1] + " " + line.strip()

    return ret


class OperationsUserDoc(Directive):

    def run(self) -> List[Node]:

        try:
            from mantidimaging.core.operations.loader import load_filter_packages
        except ImportError as exc:
            raise ValueError("operations_user_doc could not import load_filter_packages") from exc

        env = self.state.document.settings.env
        env.note_dependency(__file__)

        rst_lines = []

        operations = load_filter_packages()
        for op in operations:
            env.note_dependency(inspect.getfile(op))
            # Title
            rst_lines += make_heading(op.filter_name, "-")

            # Description from class doc string
            rst_lines += split_lines(inspect.cleandoc(op.__doc__))
            rst_lines.append("")

            # parameters from filter_func
            if op.filter_func.__doc__ is not None:
                rst_lines += get_params(op.filter_func.__doc__)
                rst_lines.append("")

            rst_lines.append(f":class:`{op.filter_name} API docs<mantidimaging.core.operations.{op.__module__}>`")
            rst_lines.append("")

        rst = ViewList()
        for n, rst_line in enumerate(rst_lines):
            rst.append(rst_line, "generated.rst", n)

        node = nodes.section()
        node.document = self.state.document

        nested_parse_with_titles(self.state, rst, node)

        return node.children


def setup(app):
    app.add_directive("operations_user_doc", OperationsUserDoc)

    return {
        'version': '0.1',
        'parallel_read_safe': True,
        'parallel_write_safe': True,
    }
