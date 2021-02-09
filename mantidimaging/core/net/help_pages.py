# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later

from PyQt5.QtCore import QUrl
from PyQt5.QtGui import QDesktopServices

DOCS_BASE = "https://mantidproject.github.io/mantidimaging"
SECTION_API = f"{DOCS_BASE}/api/"
SECTION_USER_GUIDE = f"{DOCS_BASE}/user_guide/"


def open_api_webpage(page_url: str):
    open_help_webpage(SECTION_API, page_url)


def open_help_webpage(section_url: str, page_url: str):
    url = QUrl(f"{section_url}{page_url}.html")
    if not QDesktopServices.openUrl(url):
        raise RuntimeError(f"Url could not be opened: {url.toString()}")
