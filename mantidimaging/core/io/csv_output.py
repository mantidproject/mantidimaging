# Copyright (C) 2024 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations
from typing import IO

import numpy as np


class CSVOutput:

    def __init__(self) -> None:
        self.columns: dict[str, np.ndarray] = {}
        self.num_rows: int | None = None
        self.units: dict[str, str] = {}

    def add_column(self, name: str, values: np.ndarray, units: str) -> None:
        as_column = values.reshape((-1, 1))
        if self.num_rows is not None and as_column.size != self.num_rows:
            raise ValueError('Column sizes must match')

        if units:
            self.units[name] = units

        self.num_rows = as_column.size if self.num_rows is None else self.num_rows
        self.columns[name] = as_column

    def write(self, outstream: IO[str]) -> None:
        header = ','.join(self.columns.keys())
        units = ','.join(self.units.values())
        outstream.write('# ' + header + '\n' + '# ' + units + '\n')
        data = np.hstack(list(self.columns.values()))
        np.savetxt(outstream, data, fmt='%s', delimiter=',')
