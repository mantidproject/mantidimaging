from __future__ import (absolute_import, division, print_function)

from PyQt5.QtCore import Qt, QAbstractTableModel, QModelIndex

from mantidimaging.core.cor_tilt import (
        CorTiltDataModel, Field, FIELD_NAMES)


class CorTiltPointQtModel(QAbstractTableModel, CorTiltDataModel):
    """
    Qt data model for COR/Tilt finding.
    """

    def populate_slice_indices(self, begin, end, count, cor=0.0):
        self.beginResetModel()
        super(CorTiltPointQtModel, self).populate_slice_indices(begin, end, count, cor)
        self.endResetModel()

    def sort_points(self):
        self.layoutAboutToBeChanged.emit()
        super(CorTiltPointQtModel, self).sort_points()
        self.layoutChanged.emit()

    def set_point(self, idx, slice_idx=None, cor=None):
        super(CorTiltPointQtModel, self).set_point(idx, slice_idx, cor)
        self.dataChanged.emit(self.index(idx, 0), self.index(idx, 1))

    def columnCount(self, parent=None):
        return len(Field)

    def rowCount(self, parent):
        if parent.isValid():
            return 0
        return self.num_points

    def flags(self, index):
        flags = super(CorTiltPointQtModel, self).flags(index)
        flags |= Qt.ItemIsEditable
        return flags

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None

        col = index.column()

        if role == Qt.DisplayRole:
            return self._points[index.row()][col]

        elif role == Qt.ToolTipRole:
            col_field = Field(col)
            if col_field == Field.SLICE_INDEX:
                return 'Slice index (y coordinate of projection)'
            elif col_field == Field.CENTRE_OF_ROTATION:
                return 'Centre of rotation for specific slice'
            return ''

    def setData(self, index, val, role=Qt.EditRole):
        if role != Qt.EditRole:
            return False

        self.clear_results()

        col = index.column()
        col_field = Field(col)

        proper_value = None
        try:
            if col_field == Field.SLICE_INDEX:
                proper_value = int(val)
            elif col_field == Field.CENTRE_OF_ROTATION:
                proper_value = float(val)
        except ValueError:
            return False

        self._points[index.row()][col] = proper_value

        self.dataChanged.emit(index, index)

        self.sort_points()

        return True

    def insertRows(self, row, count, parent=None):
        self.beginInsertRows(
                parent if parent is not None else QModelIndex(),
                row,
                row + count - 1)

        for _ in range(count):
            self.add_point(row)

        self.endInsertRows()

    def removeRows(self, row, count, parent=None):
        if self.empty:
            return

        self.beginRemoveRows(
                parent if parent is not None else QModelIndex(),
                row,
                row + count - 1)

        for _ in range(count):
            self.remove_point(row)

        self.endRemoveRows()

    def removeAllRows(self, parent=None):
        if self.empty:
            return

        self.beginRemoveRows(
                parent if parent else QModelIndex(),
                0,
                self.num_points - 1)

        self.clear_points()

        self.endRemoveRows()

    def appendNewRow(self, slice_idx, cor=0):
        self.insertRows(self.num_points, 1)

        self.setData(
                self.index(self.num_points - 1, Field.SLICE_INDEX.value),
                slice_idx)

        self.set_cor_at_slice(slice_idx, cor)

    def headerData(self, section, orientation, role):
        if orientation != Qt.Horizontal:
            return None

        if role != Qt.DisplayRole:
            return None

        return FIELD_NAMES[Field(section)]
