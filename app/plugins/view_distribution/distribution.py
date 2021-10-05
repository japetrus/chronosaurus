from PySide2 import QtCore, QtGui, QtWidgets, QtPrintSupport
from PySide2.QtWidgets import QWidget, QCheckBox, QGroupBox, QFormLayout
from PySide2.QtGui import QPainterPath, QPen, QBrush, QColor
from PySide2.QtCore import Qt, QPointF
from PySide2.QtUiTools import QUiLoader
from QCustomPlot_PySide import *

from app.widgets.ControlWidget import PlotControlWidget
from app.widgets.PenButton import PenButton
from app.widgets.PenDialog import PenDialog
from app.widgets.ColumnComboBox import ColumnComboBox
from app.widgets.ViewWidget import ARViewWidget
from app.preferences import applyStyleToPlot
from app.data import datasets
from app.datatypes import ColumnTypes

import numpy as np
import os
from scipy.stats import gaussian_kde
import pickle

def gaussian(x, mu, sig):
    return np.exp(-np.power(x - mu, 2.) / (2 * np.power(sig, 2.)))

class Distribution(ARViewWidget):

    def __init__(self, parent=None):
        super(Distribution, self).__init__(QCustomPlot(), parent)
        self.plot = self.widget()
        self.plot.axisRect().setupFullAxesBox(True)
        applyStyleToPlot(self.plot)

        self.setProperty('hist', True)
        self.setProperty('histBins', 25)
        self.setProperty('histPen', QPen(Qt.blue))
        self.setProperty('histBrush', QBrush(QColor(0, 0, 255, 190)))
        self.setProperty('pdp', False)
        self.setProperty('pdpPen', QPen(Qt.blue))
        self.setProperty('pdpBrush', QBrush(QColor(0, 0, 255, 190)))
        self.setProperty('kde', True)
        self.setProperty('kdePen', QPen(Qt.red))
        self.setProperty('kdeBrush', QBrush(QColor(255, 0, 0, 190)))
        self.setProperty('kdeBW', 'Adaptive')
        self.setProperty('ticks', True)
        self.setProperty('tickLength', 8)
        self.setProperty('tickPen', QPen(Qt.black))

        self.propertyChanged.connect(self.updateView)

    def createControlWidget(self):
        print('create control widget for DISTRIBUTION')
        return DistributionProperties(self)

    def addDataset(self, name):
        self.dsname = name
        self.updateView()

    def updateView(self):
        try:
            df = datasets[self.dsname]
            dataColumn = self.property('dataColumn')
            d = df[dataColumn].values
            errColumn = self.property('errorColumn')
            ed = df[errColumn].values
        except:
            return

        self.plot.clearGraphs()
        self.plot.clearPlottables()

        if self.property('hist'):
            h, binEdges = np.histogram(d, bins=int(self.property('histBins')))
            bars = QCPBars(self.plot.xAxis, self.plot.yAxis2)
            bw = np.mean(np.diff(binEdges))
            bars.setData(binEdges[:-1]+bw/2, h)
            bars.setWidth(bw)
            bars.setPen(self.property('histPen'))
            bars.setBrush(self.property('histBrush'))
            self.plot.incref(bars)

        if self.property('pdp'):
            x = np.linspace(np.min(d) - 0.2*np.ptp(d), np.max(d) + 0.2*np.ptp(d), 1000)
            y = np.zeros(len(x))
            for (dv, ev) in zip(d, ed):
                y += gaussian(x, dv, ev)

            y /= np.sum(y)
            self.pdpGraph = self.plot.addGraph()
            self.pdpGraph.setData(x, y)
            self.pdpGraph.setPen(self.property('pdpPen'))
            self.pdpGraph.setBrush(self.property('pdpBrush'))

        if self.property('kde'):
            self.kdeGraph = self.plot.addGraph()        
            k = gaussian_kde(d)
            x = np.linspace(np.min(d) - 0.2*np.ptp(d), np.max(d) + 0.2*np.ptp(d), 1000)
            y = k(x)
            self.kdeGraph.setData(x, y)
            self.kdeGraph.setPen(self.property('kdePen'))
            self.kdeGraph.setBrush(self.property('kdeBrush'))

        if self.property('ticks'):
            self.ticksGraph = self.plot.addGraph()
            self.ticksGraph.setData(d, np.full(len(d), 0))
            self.ticksGraph.setLineStyle(QCPGraph.lsNone)
            ss = QCPScatterStyle(QCPScatterStyle.ssCustom)
            pp = QPainterPath(QPointF(0, -int(self.property('tickLength'))))
            pp.lineTo(QPointF(0, 0))
            ss.setCustomPath(pp)
            if self.property('tickPen'):
                ss.setPen(self.property('tickPen'))
            self.ticksGraph.setScatterStyle(ss)

        self.plot.rescaleAxes()
        self.plot.replot()

    def saveState(self):
        s = {
            'dataColumn': self.property('dataColumn'),
            'errorColumn': self.property('errorColumn'),
            'datasetName': self.dsname,
            'plotSettings': self.plot.saveState()
        }
        return pickle.dumps(s)

    def restoreState(self, state):
        s = pickle.loads(state)
        self.setProperty('dataColumn', s['dataColumn'])
        self.setProperty('errorColumn', s['errorColumn'])
        self.addDataset(s['datasetName'])
        self.plot.restoreState(s['plotSettings'])


class DistributionProperties(PlotControlWidget):
    def __init__(self, view, parent=None):
        super().__init__(view, parent)

        self.dataComboBox = ColumnComboBox(self, ctypes=ColumnTypes.Value)
        self.dataComboBox.columnChanged.connect(lambda s: view.setProperty('dataColumn', s))
        self.errComboBox = ColumnComboBox(self, ctypes=ColumnTypes.Error)
        self.errComboBox.columnChanged.connect(lambda s: view.setProperty('errorColumn', s))

        self.layout().insertRow(1, 'Data', self.dataComboBox)
        self.layout().insertRow(2, 'Error', self.errComboBox)

        loader = QUiLoader()
        loader.registerCustomWidget(PenButton)
        options = loader.load(os.path.dirname(__file__) + '/distribution_control.ui', self)
        options.setContentsMargins(9, 9, 9, 9)
        self.tabWidget.insertTab(1, options, 'Options')

        def getPenForProperty(control, pname, pvalue=QPen(Qt.blue)):
            d = PenDialog(pvalue)
            if d.exec_() == PenDialog.Rejected:
                return
            control.setPen(d.selectedPen())
            view.setProperty(pname, d.selectedPen())

        def getBrushForProperty(control, pname, pvalue=QBrush(Qt.blue)):
            from PySide2.QtWidgets import QColorDialog
            d = QColorDialog(self, pvalue)

            if d.exec_() == QColorDialog.Rejected:
                return

            control.setStyleSheet('QToolButton { background: rgb(%i,%i,%i); }'%(d.selectedColor().red(), d.selectedColor().green(), d.selectedColor().blue()))
            view.setProperty(pname, d.selectedColor())

        def toggleGroupBox(box, b):
            if b:
                box.setStyleSheet('')
            else:
                box.setStyleSheet('QGroupBox { border: 0; }')
                        
            [c.setVisible(b) for c in box.children() if isinstance(c, QWidget)]

        # Histogram
        options.histGroupBox.clicked.connect(lambda b: view.setProperty('hist', b))
        options.histGroupBox.clicked.connect(lambda b: toggleGroupBox(options.histGroupBox, b))
        options.histBinsSpinBox.valueChanged[int].connect(lambda v: view.setProperty('histBins', v))
        options.histBorderButton.clicked.connect(lambda: getPenForProperty(options.histBorderButton, 'histPen'))
        options.histFillButton.clicked.connect(lambda: getBrushForProperty(options.histFillButton, 'histBrush'))

        # PDP
        options.pdpGroupBox.clicked.connect(lambda b: view.setProperty('pdp', b))
        options.pdpGroupBox.clicked.connect(lambda b: toggleGroupBox(options.pdpGroupBox, b))
        options.pdpPenButton.clicked.connect(lambda: getPenForProperty(options.pdpPenButton, 'pdpPen'))
        options.pdpBrushButton.clicked.connect(lambda: getBrushForProperty(options.pdpBrushButton, 'pdpBrush'))

        # KDE
        options.kdeGroupBox.clicked.connect(lambda b: view.setProperty('kde', b))
        options.kdeGroupBox.clicked.connect(lambda b: toggleGroupBox(options.kdeGroupBox, b))
        options.kdePenButton.clicked.connect(lambda: getPenForProperty(options.kdePenButton, 'kdePen'))
        options.kdeBrushButton.clicked.connect(lambda: getBrushForProperty(options.kdeBrushButton, 'kdeBrush'))
        options.kdeBWComboBox.activated[str].connect(lambda s: view.setProperty('kdeBW', s))

        # Ticks
        options.ticksGroupBox.clicked.connect(lambda b: view.setProperty('ticks', b))
        options.ticksGroupBox.clicked.connect(lambda b: toggleGroupBox(options.ticksGroupBox, b))
        options.tickLengthSpinBox.valueChanged[int].connect(lambda v: view.setProperty('tickLength', v))
        options.tickPenButton.clicked.connect(lambda: getPenForProperty(options.tickPenButton, 'tickPen'))

