from PySide2.QtCore import QAbstractTableModel, QSortFilterProxyModel, Qt, QSettings, QModelIndex
from PySide2.QtGui import QColor
import pandas as pd
import numpy as np
import re

class PandasModel(QAbstractTableModel):

    _float_precisions = {
        "float16": np.finfo(np.float16).precision - 2,
        "float32": np.finfo(np.float32).precision - 1,
        "float64": np.finfo(np.float64).precision - 1
    }

    column_list = []
    _data = pd.DataFrame()

    def __init__(self, data, columns=[], parent=None):
        QAbstractTableModel.__init__(self, parent)
        self._data = data
        self.column_list = columns

    def get_data_frame(self):
        return self._data

    def set_data_frame(self, data):
        self.beginResetModel()
        self._data = data
        self.endResetModel()

    def rowCount(self, parent=None, *args, **kwargs):
        return len(self._data.index)

    def columnCount(self, parent=None):
        if not self.column_list:
            return self._data.columns.size
        else:
            return len(self.column_list)

    def headerData(self, p_int, Qt_Orientation, role=None):
        if role == Qt.DisplayRole and Qt_Orientation == Qt.Horizontal:
            if not self.column_list:
                return self._data.columns[p_int]
            else:
                return self.column_list[p_int]

        if role == Qt.DisplayRole and Qt_Orientation == Qt.Vertical:
            return self._data.index[p_int]

        return None

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None

        if role == Qt.DisplayRole:
            if not self.column_list:
                column_name = self._data.columns[index.column()]
                column_index = self._data.columns.get_loc(column_name)
            else:
                column_name = self.column_list[index.column()]
                column_index = self._data.columns.get_loc(column_name)

            val = self._data.iloc[index.row(), column_index]
            if type(val) == np.float64:
                if val != val:
                    return '-'

                val = round(float(val), self._float_precisions['float64'])
                return val
            else:
                return str(val)
        elif role == Qt.BackgroundRole and hasattr(self, 'row_colors'):
            return self.row_colors[index.row()]

        return None




class PandasProxyModel(QSortFilterProxyModel):

    def __init__(self, parent=None):
        QSortFilterProxyModel.__init__(self, parent)
        self.rowFilter = ''
        self.colFilter = ''
    
    def setRowFilter(self, rf):
        self.rowFilter = rf
        self.invalidate()

    def setColFilter(self, cf):
        self.colFilter = cf
        self.invalidate()

    def filterAcceptsRow(self, p_int, index):

        header = str(self.sourceModel().headerData(p_int, Qt.Vertical, role=Qt.DisplayRole))

        if not header:
            print('not header?')
            return True

        if not self.rowFilter:
            return True
        
        return re.search(self.rowFilter, header) is not None

    def filterAcceptsColumn(self, source_column: int, source_parent: QModelIndex) -> bool:
        header = str(self.sourceModel().headerData(source_column, Qt.Horizontal, role=Qt.DisplayRole))

        if not header:
            print('not header?')
            return True

        if not self.colFilter:
            return True

        return re.search(self.colFilter, header) is not None


class PandasImportModel(PandasModel):
    column_assignments = {}

    def __init__(self, data_frame, parent=None):
        PandasModel.__init__(self, data_frame, [], parent)

        assert isinstance(self._data, pd.DataFrame)

        settings = QSettings()
        self.column_assignments = settings.value("previous_column_assignments", {})

        keys = [k for k in self.column_assignments.keys()]

        for key in keys:
            if key not in self._data.columns:
                del self.column_assignments[key]

    def rowCount(self, parent=None):
        return PandasModel.rowCount(self) + 1

    def headerData(self, p_int, Qt_Orientation, role=None):
        if role == Qt.DisplayRole and Qt_Orientation == Qt.Horizontal:
            return self._data.columns[p_int]

        return None

    def data(self, index, role=Qt.DisplayRole):
        if index.row() == 0 and role == Qt.DisplayRole:
            column_name = self._data.columns[index.column()]
            if column_name in self.column_assignments.keys():
                return self.column_assignments[column_name]
            else:
                return "Not assigned"

        if index.row() == 0 and role == Qt.BackgroundColorRole:
            return QColor(155, 155, 155)

        if index.isValid() and role == Qt.DisplayRole:
            superindex = self.index(index.row() - 1, index.column())
            return super().data(superindex, role)

        # if index.isValid() and role == Qt.DisplayRole:
        #    return QVariant(str(self._data.values[index.row()-1][index.column()]))

        return None

    def setData(self, index, value, role=Qt.DisplayRole):
        column_name = self._data.columns[index.column()]
        if value == 'Not assigned':
            self.column_assignments[column_name] = None
        else:
            self.column_assignments[column_name] = value

        print(self.column_assignments)

    def flags(self, index):
        if index.row() == 0:
            return Qt.ItemIsEditable | Qt.ItemIsEnabled
        else:
            return Qt.ItemIsEnabled        

class PandasImportProxyModel(QSortFilterProxyModel):

    def __init__(self, parent=None):
        QSortFilterProxyModel.__init__(self, parent)
        self.colFilter = None

    def setColumnFilter(self, colFilter):
        self.colFilter = colFilter
        self.invalidate()

    def filterAcceptsRow(self, p_int, index):

        header = str(self.sourceModel().headerData(p_int, Qt.Vertical, role=Qt.DisplayRole))

        if p_int == 0:
            return True

        if not header:
            print('not header?')
            return True

        if not self.filterRegExp().pattern():
            return True

        return self.filterRegExp().pattern() in header      

    def filterAcceptsColumn(self, p_int, index):
        header = str(self.sourceModel().headerData(p_int, Qt.Horizontal, role=Qt.DisplayRole))

        if not header:
            print('not header?')
            return True

        if not self.colFilter:
            return True

        return self.colFilter in header