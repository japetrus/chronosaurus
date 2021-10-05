from PySide2.QtWidgets import QStyledItemDelegate, QLineEdit, QStyle, QApplication
from PySide2.QtGui import QPalette, QBrush
from PySide2.QtCore import Qt, QRect
from ..models.datasetsmodel import DataFrameRole

class DatasetDelegate(QStyledItemDelegate):
    def createEditor(self, parent, option, index):
        name = str(index.data(Qt.DisplayRole).toString())
        editor = QLineEdit(parent=parent)
        editor.setText(name)
        return editor

    def updateEditorGeometry(self, editor, option, index):
        editor.setGeometry(option.rect) 

    def paint(self, painter, option, index):
        painter.save()
        self.initStyleOption(option, index)

        rect = option.rect

        if option.state & QStyle.State_Selected:
            painter.setPen(option.palette.color(QPalette.HighlightedText))
            painter.fillRect(option.rect, QBrush(option.palette.color(QPalette.Highlight)))
        else:
            painter.setPen(option.palette.color(QPalette.Text))

        line0 = index.data(Qt.DisplayRole)
        df = index.data(DataFrameRole)
        try:
            line1 = '%i measurements, %s'%(len(df), ', '.join(df.datatypes))
        except:
            line1 = '%i measurements'%len(df)

        rect = rect.adjusted(5, 0, -5, -5)

        normalFont = painter.font()
        painter.drawText(QRect(rect.left(), rect.top()+rect.height()*2/3, rect.width(), rect.height()*1/3),
                          option.displayAlignment, line1)
                     

        bigFont = normalFont
        bigFont.setPointSize(bigFont.pointSize()*1.5)
        painter.setFont(bigFont)
        painter.drawText(QRect(rect.left(), rect.top(), rect.width(), rect.height()*2/3),
                          option.displayAlignment, line0)
        
        painter.restore()
        


    def sizeHint(self, option, index):
        s = super().sizeHint(option, index)
        s.setHeight(option.fontMetrics.height()*3)
        return s