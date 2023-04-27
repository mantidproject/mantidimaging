# Copyright (C) 2023 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

from typing import Optional

from PyQt5.QtCore import QUrl
from PyQt5.QtGui import QDesktopServices

DOCS_BASE = "https://mantidproject.github.io/mantidimaging"
SECTION_USER_GUIDE = f"{DOCS_BASE}/user_guide/"


def open_user_operation_docs(operation_name: str) -> None:
    page_url = "operations/index"
    section = operation_name.lower().replace(" ", "-")
    open_help_webpage(SECTION_USER_GUIDE, page_url, section)


def open_help_webpage(section_url: str, page_url: str, section: Optional[str] = None) -> None:
    if section is not None:
        url = f"{section_url}{page_url}.html#{section}"
    else:
        url = f"{section_url}{page_url}.html"

    if not QDesktopServices.openUrl(QUrl(url)):
        raise RuntimeError(f"Url could not be opened: {url}")
