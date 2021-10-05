
from PySide2.QtWidgets import QItemDelegate, QComboBox, QToolButton, QMenu, QAction
from app.systems import Columns


class ColumnsDelegate(QItemDelegate):

    def __init__(self, parent):
        QItemDelegate.__init__(self, parent)
        #self.editorItems = Columns.column_list
        #self.editorItems.insert(0, "Sample ID")
        #self.editorItems.insert(0, "Not assigned")

    def createEditor(self, parent, option, index):
        # combo = QComboBox(parent)
        # combo.addItems(self.editorItems)
        # combo.currentIndexChanged.connect(self.currentIndexChanged)
        # return combo

        button = QToolButton(parent)
        menu = QMenu(button)
        button.setMenu(menu)
        button.setPopupMode(QToolButton.InstantPopup)

        menu.addAction('Sample ID')
        menu.addAction('Not specified')
        menu.addSeparator()

        for system in Columns.namesForSystem.keys():
            sysMenu = QMenu(system, menu)
            for col in Columns.titlesForSystem[system]:
                sysMenu.addAction(col)
            menu.addMenu(sysMenu)

        menu.triggered.connect(lambda a: self.setColumn(a.text()))
        menu.triggered.connect(lambda a: button.setText(a.text()))
        return button
        
    def setColumn(self, name):
        self.column = name
        self.commitData.emit(self.sender())

    def setEditorData(self, editor, index):
        editor.blockSignals(True)
        #editor.setCurrentText(index.model().data(index))
        editor.setText(index.model().data(index))
        editor.blockSignals(False)

    def setModelData(self, editor, model, index):
        model.setData(index, self.column)

    def currentIndexChanged(self):
        self.commitData.emit(self.sender())