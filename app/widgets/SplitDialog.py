from ..ui.SplitDialog_ui import Ui_Dialog
from PySide2.QtWidgets import QDialog
from app.models.pandasmodel import PandasModel
from app.data import datasets
from difflib import SequenceMatcher
from PySide2.QtCore import Qt
from PySide2.QtGui import QColor, QBrush
from math import fmod

class SplitDialog(QDialog, Ui_Dialog):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self.pushButton.clicked.connect(self.auto_split)        

    def set_data(self, dsname):
        self.model = PandasModel(datasets[dsname], parent=self)
        self.tableView.setModel(self.model)
        self.columnComboBox.clear()
        self.columnComboBox.addItems(datasets[dsname].columns)

    def random_colors(self, count):
        colors = []

        current_hue = 0.0

        for i in range(count):
            colors.append(QColor.fromHslF(current_hue, 1.0, 0.5))
            current_hue += 0.618033988749895
            current_hue = fmod(current_hue, 1.0)

        return colors


    def auto_split(self):
        ratio = self.ratioSpinBox.value()

        matched_names = {}

        for i, name in enumerate(self.model.get_data_frame()[self.columnComboBox.currentText()]):
            print('Checking %i %s'%(i, name))
            
            matched = False

            for matched_name in matched_names:
                if SequenceMatcher(None, name, matched_name).ratio() > ratio:
                    matched_names[matched_name].append(i)
                    matched = True
                    print('Matched %s to %s'%(name, matched_name))
            
            if not matched:
                matched_names[name] = [i]
                print('Could not match %s, started a new match group'%(name))

        print(matched_names)

        row_colors = [QBrush(Qt.transparent)]*self.model.rowCount()

        colors = [QBrush(c) for c in self.random_colors(len(row_colors))]        

        for matched_name in matched_names:
            c = colors.pop()
            for i in matched_names[matched_name]:
                row_colors[i] = c

        self.model.row_colors = row_colors

        self.matched_names = matched_names
        

            
            


