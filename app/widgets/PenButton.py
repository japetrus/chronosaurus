from PySide2.QtWidgets import QToolButton
from PySide2.QtGui import QPainter, QPen
from PySide2.QtCore import QPointF

class PenButton(QToolButton):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setText('')
        self.pen = QPen()

    def setPen(self, p):
        self.pen = p
        self.repaint()

    def paintEvent(self, e):
        QToolButton.paintEvent(self, e)
        painter = QPainter(self)
        painter.setPen(self.pen)
        painter.drawLine(
            QPointF(e.rect().left() + 6, e.rect().center().y()),
            QPointF(e.rect().right() - 6, e.rect().center().y()))
