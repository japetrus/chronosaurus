from PySide2.QtWidgets import QColorDialog, QWidget, QFormLayout, QSpinBox, QComboBox
from PySide2.QtCore import Qt

class PenDialog(QColorDialog):

    def __init__(self, pen, parent=None):
        super().__init__(parent)
        self.pen = pen
        self.setOption(QColorDialog.DontUseNativeDialog)
        self.setCurrentColor(self.pen.color())

        self.w = QWidget(self)
        self.w.setLayout(QFormLayout())

        self.widthSpinBox = QSpinBox(self)
        self.widthSpinBox.setRange(0, 50)
        self.widthSpinBox.setValue(pen.width())
        self.widthSpinBox.valueChanged.connect(lambda v: self.pen.setWidth(v))
        self.w.layout().addRow('Line width', self.widthSpinBox)

        self.styleComboBox = QComboBox(self)
        self.styleComboBox.addItem('Solid', Qt.SolidLine)
        self.styleComboBox.addItem('Dotted', Qt.DotLine)
        self.styleComboBox.addItem('Dashed', Qt.DashLine)
        self.styleComboBox.addItem('Dash Dotted', Qt.DashDotLine)
        self.styleComboBox.addItem('Dash Dot Dotted', Qt.DashDotDotLine)
        self.styleComboBox.activated.connect(lambda i: self.pen.setStyle(Qt.PenStyle(self.styleComboBox.currentData())))
        self.w.layout().addRow('Line style', self.styleComboBox)

        self.layout().insertWidget(0, self.w)

    def selectedPen(self):
        p = self.pen
        p.setColor(self.selectedColor())
        return p



    


