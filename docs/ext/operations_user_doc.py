# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later

from docutils import nodes
from docutils.parsers.rst import Directive
"""Custom extension to add nicely formatted documentation for the operations.

Use:
.. operations_user_doc::

in a documentation rst file to generate.
"""


class OperationsUserDoc(Directive):
    def run(self):

        paragraphs = []
        try:
            from mantidimaging.core.operations.loader import load_filter_packages
        except ImportError:
            raise ValueError("operations_user_doc could not import load_filter_packages")

        operations = load_filter_packages()
        for op in operations:
            paragraphs.append(nodes.paragraph(text=op.filter_name))

        return paragraphs


def setup(app):
    app.add_directive("operations_user_doc", OperationsUserDoc)

    return {
        'version': '0.1',
        'parallel_read_safe': True,
        'parallel_write_safe': True,
    }
