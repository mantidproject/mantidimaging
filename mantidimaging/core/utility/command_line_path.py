# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
class CommandLinePath:
    _instance = None
    images_path = ""

    def __new__(cls, path: str = ""):
        """
        Creates a singleton for storing the path from the command line argument.
        """
        if cls._instance is None:
            cls._instance = super(CommandLinePath, cls).__new__(cls)
            cls.images_path = path
        return cls._instance

    @classmethod
    def path(cls) -> str:
        """
        Returns the command line images path.
        """
        return cls.images_path
