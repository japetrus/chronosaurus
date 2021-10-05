from QCustomPlot_PySide import QCPItemText
from PySide2.QtGui import QTextDocument, QPen
from PySide2.QtCore import QPointF, Qt, QPoint

class QCPItemRichText(QCPItemText):

    def __init__(self, parent):
        super().__init__(parent)

    def draw(self, painter):
        pos = self.position().pixelPosition()
        transform = painter.transform()
        transform.translate(pos.x(), pos.y())
        if self.rotation() != 0:
            transform.rotate(self.rotation())

        td = QTextDocument()
        td.setHtml(self.text())

        painter.setFont(self.mainFont())
        textRect = td.documentLayout().frameBoundingRect(td.rootFrame())
        textBoxRect = textRect.adjusted(-self.padding().left(), -self.padding().top(), self.padding().right(), self.padding().bottom())
        textPos = self.getTextDrawPoint(QPointF(0, 0), textBoxRect, self.positionAlignment())
        textRect.moveTopLeft(textPos.toPoint() + QPoint(self.padding().left(), self.padding().top()))
        textBoxRect.moveTopLeft(textPos.toPoint())
        clipPad = self.mainPen().widthF()
        boundingRect = textBoxRect.adjusted(-clipPad, -clipPad, clipPad, clipPad)
        if transform.mapRect(boundingRect).intersects(painter.transform().mapRect(self.clipRect())):
            painter.setTransform(transform)
            if (self.mainBrush().style() != Qt.NoBrush and self.mainBrush().color().alpha() != 0) or (self.mainPen().style() != Qt.NoPen and self.mainPen().color().alpha() != 0):
                painter.setPen(self.mainPen())
                painter.setBrush(self.mainBrush())
                painter.drawRect(textBoxRect)

            painter.setBrush(Qt.NoBrush)
            painter.setPen(QPen(self.mainColor()))

        richTextPoint = QPointF(0., 0.)

        if self.positionAlignment() & Qt.AlignHCenter:
            richTextPoint.setX(richTextPoint.x() - textBoxRect.width()/2.0)
        elif self.positionAlignment() & Qt.AlignRight:
            richTextPoint.setX(richTextPoint.x() - textBoxRect.width())

        if self.positionAlignment() & Qt.AlignVCenter:
            richTextPoint.setY(richTextPoint.y() - textBoxRect.height()/2.0)
        elif self.positionAlignment() & Qt.AlignBottom:
            richTextPoint.setY(richTextPoint.y() - textBoxRect.height())

        painter.translate(richTextPoint)
        td.drawContents(painter)
