from PySide2.QtWidgets import QComboBox
from PySide2.QtCore import Signal

from itertools import chain

from app.data import datasets
from app.datatypes import ColumnTypes, Columns
from app.dispatch import dispatch

class ColumnComboBox(QComboBox):

    columnChanged = Signal(str)

    def __init__(self, parent=None, ctypes=ColumnTypes.All):
        QComboBox.__init__(self, parent)
        self.colTypes = ctypes
        dispatch.datasetsChanged.connect(self.updateColumns)
        self.updateColumns()
        self.activated[str].connect(lambda s: self.columnChanged.emit(s))

    def updateColumns(self):
        columns = [list(datasets[dfname].columns) for dfname in datasets]
        columns = list(set(chain(*columns)))
        columns = [c for c in columns if c]
        columns.sort()
        columns = [c for c in columns if c in Columns.for_type[self.colTypes]]

        self.clear()
        if columns:
            self.addItems(columns)
