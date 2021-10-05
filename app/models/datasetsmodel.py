from PySide2.QtCore import QAbstractListModel, QSortFilterProxyModel, Qt, QSettings
from PySide2.QtGui import QColor, QBrush
import pandas as pd
import numpy as np

from app.data import datasets
from app.dispatch import dispatch

DataFrameRole = Qt.UserRole + 1

class DatasetsModel(QAbstractListModel):

    def __init__(self, parent=None):
        QAbstractListModel.__init__(self, parent)
        dispatch.datasetsChanged.connect(self.refresh)

    def rowCount(self, parent=None, *args, **kwargs):
        return len(datasets)

    def data(self, index, role=Qt.DisplayRole):        
        if not index.isValid():
            return
            
        if role == Qt.DisplayRole:
            return list(datasets.keys())[index.row()]
        elif role == DataFrameRole:
            return datasets[list(datasets.keys())[index.row()]]
        return None

    def refresh(self):
        self.beginResetModel()
        self.endResetModel()