from PySide2.QtWidgets import QTableView, QLabel, QFormLayout, QToolButton, QInputDialog, QFileDialog, QLineEdit
from app.models.pandasmodel import PandasModel, PandasProxyModel
from app.widgets.ControlWidget import ControlWidget
from PySide2.QtCore import Signal
from app.data import datasets
from app.dispatch import dispatch
import pickle

class DataTable(QTableView):

    dataChanged = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.dsname = None
        self.setWindowTitle('Data table')
        self.pmodel = PandasProxyModel(self)

    def addDataset(self, name):
        self.dsname = name
        self.model = PandasModel(datasets[name], None, self)
        self.pmodel.setSourceModel(self.model)
        self.setModel(self.pmodel)
        self.dataChanged.emit()

    def widget(self):
        return self

    def createControlWidget(self):
        return DataTableControlWidget(self)

    def saveState(self):
        s = {
            'dsname': self.dataset_name
        }
        return pickle.dumps(s)

    def restoreState(self, state_pickle):
        s = pickle.loads(state_pickle)
        self.addDataset(s['dsname'])        


class DataTableControlWidget(ControlWidget):
    def __init__(self, view, parent=None):
        super().__init__(view, parent)
        self.label = QLabel(self)
        self.layout().insertRow(1, 'Dataset', self.label)
        self.fromSelectionButton = QToolButton(self)
        self.fromSelectionButton.setText('New dataset from selection')
        self.layout().insertRow(2, 'Tools', self.fromSelectionButton)
        self.fromSelectionButton.clicked.connect(self.newFromSelection)

        self.rowFilterEdit = QLineEdit(self)
        self.layout().insertRow(3, 'Row filter', self.rowFilterEdit)
        self.rowFilterEdit.textEdited.connect(lambda t: view.pmodel.setRowFilter(t))
        self.colFilterEdit = QLineEdit(self)
        self.layout().insertRow(4, 'Column filter', self.colFilterEdit)
        self.colFilterEdit.textEdited.connect(lambda t: view.pmodel.setColFilter(t))

        self.exportFormatComboBox.clear()
        self.exportFormatComboBox.addItems(['Excel', 'csv', 'html'])
            
    def updateState(self):
        super().updateState()
        self.label.setText(self.view.dsname)

    def newFromSelection(self):
        rows = [ri.row() for ri in self.view.selectionModel().selectedRows(0)]
        new_df = datasets[self.view.dsname].iloc[rows]

        t, ok = QInputDialog.getText(self, 'Dataset name', 'New dataset name')
        if not ok:
            return

        datasets[t] = new_df
        dispatch.datasetsChanged.emit()

    def export(self):
        f = self.exportFormatComboBox.currentText()
        fn, ok = QFileDialog.getSaveFileName(self, 'Export data table')
        if not ok:
            return

        if f == 'Excel':
            datasets[self.view.dsname].to_excel(fn, self.view.dsname)
        elif f == 'csv':
            datasets[self.view.dsname].to_csv(fn)
        else:
            datasets[self.view.dsname].to_html(fn)
