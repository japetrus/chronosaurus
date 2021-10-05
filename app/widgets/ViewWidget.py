from PySide2.QtWidgets import QWidget, QBoxLayout, QSizePolicy, QSpacerItem, QMenu, QAction, QInputDialog
from PySide2.QtGui import QResizeEvent
from PySide2.QtCore import Signal, Qt, QSize
from QCustomPlot_PySide import *
from .ControlWidget import ControlWidget
from app import preferences
import numpy as np
from app.data import datasets
from app.dispatch import dispatch
import pandas as pd
'''
NOTE:

When using QCP from python and adding items or plottables by calling 
a constructor, e.g. QCPItemText(.., ..), you must also call
plot.incref(item). Otherwise, the object will be deleted
twice on destruction.
'''

class ViewWidget(QWidget):

    propertyChanged = Signal()
    dataChanged = Signal()
    beginProgress = Signal()
    endProgress = Signal()
    progress = Signal(int, str)
    report = Signal(tuple) # (report_name, report_text)

    def __init__(self, widget, parent=None):
        super().__init__(parent)
        self._widget = widget    
        self.setLayout(QBoxLayout(QBoxLayout.LeftToRight, self))
        self.layout().addItem(QSpacerItem(0, 0))
        self.layout().addWidget(widget)
        self.layout().addItem(QSpacerItem(0, 0))

        if isinstance(widget, QCustomPlot):
            widget.plottableClick.connect(self.processClick)
            widget.mousePress.connect(lambda ev: print(widget.plottableAt(ev.pos(), False)))

    def setProperty(self, name, value):
        QWidget.setProperty(self, name, value)
        self.propertyChanged.emit()

    def setProperties(self, props):
        for p in props:
            self.setProperty(p, props[p])

    def widget(self):
        return self._widget

    def createControlWidget(self):
        return ControlWidget(self)

    def processClick(self, pl, di, ev):
        print('processClick %s'%pl)        
        if ev.button() == Qt.RightButton:
            # If the whole plottable represents a measurement (e.g. error ellipse)
            if pl.property('dataIndex'):
                di = pl.property('dataIndex')

            m = QMenu()
            m.addAction('Delete data point', lambda: self.deletePoint(di))
            m.addAction('Move data point', lambda: self.movePoint(di))
            m.addAction('Copy data point', lambda: self.movePoint(di, preserve=True))
            m.exec_(self._widget.mapToGlobal(ev.pos()))

    def deletePoint(self, di):
        datasets[self.dsname].drop(di, axis='index', inplace=True)
        dispatch.datasetsChanged.emit()
        self.addDataset(self.dsname)

    def movePoint(self, di, preserve=False):

        newname, ok = QInputDialog.getItem(self, 'Move data point', 'New dataset name', datasets.keys(), 0, True)
        if not ok:
            return
        
        if newname not in datasets.keys():
            datasets[newname] = pd.DataFrame(columns=datasets[self.dsname].columns)

        datasets[newname].loc[di] = datasets[self.dsname].loc[di]

        if not preserve:
            self.deletePoint(di)

        dispatch.datasetsChanged.emit()

        



class ARViewWidget(ViewWidget):

    def __init__(self, widget, parent=None):
        super().__init__(widget, parent)
        self.aspect_ratio = preferences.aspectRatio #widget.size().width() / widget.size().height()

    def setAspectRatio(self, ar):
        self.aspect_ratio = ar
        re = QResizeEvent(self.geometry().size(), self.geometry().size())
        self.resizeEvent(re)

    def resizeEvent(self, e):
        w = e.size().width()
        h = e.size().height()

        if w / h > self.aspect_ratio:  # too wide
            self.layout().setDirection(QBoxLayout.LeftToRight)
            widget_stretch = h * self.aspect_ratio
            outer_stretch = (w - widget_stretch) / 2 + 0.5
        else:  # too tall
            self.layout().setDirection(QBoxLayout.TopToBottom)
            widget_stretch = w / self.aspect_ratio
            outer_stretch = (h - widget_stretch) / 2 + 0.5

        self.layout().setStretch(0, outer_stretch)
        self.layout().setStretch(1, widget_stretch)
        self.layout().setStretch(2, outer_stretch)

