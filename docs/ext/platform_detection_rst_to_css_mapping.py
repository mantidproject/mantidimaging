# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
"""
Custom Sphinx extension to render OS-specific code snippets in the documentation.

Maps RST role to CSS class applied to <kbd> element.
CSS class is toggled visible by platform_detection.js based on user's OS.
Update JS/CSS to add new roles.
"""

from typing import Any

from docutils import nodes
from sphinx.application import Sphinx

_OS_ROLES: dict[str, str] = {
    "IsMac": "shortcut-mac",
    "IsWindows": "shortcut-windows",
    "IsLinux": "shortcut-linux",
}


def _make_os_role(css_class: str):
    """
    Return a Sphinx role function that renders a <kbd> for one OS

    Args:
        css_class: CSS class to apply to the <kbd> element, which will be toggle snippet vissibility
    """

    def role(_name: str, _rawtext: str, text: str, _lineno: int, _inliner: Any, **_):
        node = nodes.raw("", f'<kbd class="shortcut {css_class}">{text}</kbd>', format="html")
        return [node], []

    return role


def setup(app: Sphinx) -> dict:
    """
    Sphinx extension setup function

    Args:
        app: Sphinx application object
    """
    for role_name, css_class in _OS_ROLES.items():
        app.add_role(role_name, _make_os_role(css_class))
    return {"parallel_read_safe": True}
