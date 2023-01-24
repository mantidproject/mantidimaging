# Copyright (C) 2023 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations
from typing import IO, Optional

import numpy as np


class CSVOutput:
    def __init__(self) -> None:
        self.columns: dict[str, np.ndarray] = {}
        self.num_rows: Optional[int] = None

    def add_column(self, name: str, values: np.ndarray) -> None:
        as_column = values.reshape((-1, 1))
        if self.num_rows is not None:
            if as_column.size != self.num_rows:
                raise ValueError("Column sizes must match")
        else:
            self.num_rows = as_column.size

        self.columns[name] = as_column

    def write(self, outstream: IO[str]) -> None:
        header = ",".join(self.columns.keys())
        data = np.hstack(list(self.columns.values()))
        np.savetxt(outstream, data, header=header, fmt="%s", delimiter=",")
