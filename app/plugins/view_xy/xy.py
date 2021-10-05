from app.widgets.ViewWidget import ARViewWidget
from app.widgets.ControlWidget import PlotControlWidget
from app.widgets.ColumnComboBox import ColumnComboBox
from app.preferences import applyStyleToPlot
from QCustomPlot_PySide import QCustomPlot, QCPGraph, QCPScatterStyle, QCPErrorBars
from app.data import datasets
from app.datatypes import ColumnTypes

class XYView(ARViewWidget):

    def __init__(self, parent=None):
        super(XYView, self).__init__(QCustomPlot(), parent)
        self.plot = self.widget()
        applyStyleToPlot(self.plot)
        self.propertyChanged.connect(self.updatePlot)

    def addDataset(self, dsname):
        self.dsname = dsname
        self.updatePlot()

    def updatePlot(self):
        xCol = self.property('xColumn')
        yCol = self.property('yColumn')
        sxCol = self.property('sxColumn')
        syCol = self.property('syColumn')
        ecCol = self.property('ecColumn')
        useEllipses = self.property('useEllipses') == 'True'

        x = datasets[self.dsname][xCol].values  
        sx = datasets[self.dsname][sxCol].values      
        y = datasets[self.dsname][yCol].values
        sy = datasets[self.dsname][syCol].values

        self.plot.clearGraphs()
        self.plot.clearPlottables()
        self.plot.clearItems()

        self.g = self.plot.addGraph()
        self.g.setData(x,y)
        self.g.setLineStyle(QCPGraph.lsNone)
        self.g.setScatterStyle(QCPScatterStyle(QCPScatterStyle.ssDisc, 8))

        self.xeb = QCPErrorBars(self.plot.xAxis, self.plot.yAxis)
        self.xeb.setErrorType(QCPErrorBars.etKeyError)
        self.xeb.setDataPlottable(self.g)
        self.xeb.setData(sx)
        self.xeb.removeFromLegend()
        self.plot.incref(self.xeb)

        self.yeb = QCPErrorBars(self.plot.xAxis, self.plot.yAxis)
        self.yeb.setErrorType(QCPErrorBars.etValueError)
        self.yeb.setDataPlottable(self.g)
        self.yeb.setData(sy)        
        self.yeb.removeFromLegend()
        self.plot.incref(self.yeb)

        self.plot.rescaleAxes()
        self.plot.replot()

    def createControlWidget(self):
        return XYControl(self)

class XYControl(PlotControlWidget):
    def __init__(self, view, parent=None):
        super().__init__(view, parent)
        self.tabWidget.setTabVisible(self.tabWidget.indexOf(self.fitTab), True)
        self.fitComboBox.currentIndexChanged.connect(lambda index: view.setProperty('FitModel', index+1))
        self.fitLabelCheckBox.clicked.connect(lambda c: view.setProperty('FitLabel', c))
        self.fitLineCheckBox.clicked.connect(lambda c: view.setProperty('FitLine', c))
        self.fitReportCheckBox.clicked.connect(lambda c: view.setProperty('FitReport', c))

        self.xComboBox = ColumnComboBox(self, ColumnTypes.Value)
        self.xComboBox.columnChanged.connect(lambda s: view.setProperty('xColumn', s))
        self.xErrComboBox = ColumnComboBox(self, ColumnTypes.Error)
        self.xErrComboBox.columnChanged.connect(lambda s: view.setProperty('sxColumn', s))

        self.layout().insertRow(1, 'X', self.xComboBox)
        self.layout().insertRow(2, 'X uncert', self.xErrComboBox)

        self.yComboBox = ColumnComboBox(self, ColumnTypes.Value)
        self.yComboBox.columnChanged.connect(lambda s: view.setProperty('yColumn', s))
        self.yErrComboBox = ColumnComboBox(self, ColumnTypes.Error)
        self.yErrComboBox.columnChanged.connect(lambda s: view.setProperty('syColumn', s))

        self.layout().insertRow(3, 'Y', self.yComboBox)
        self.layout().insertRow(4, 'Y uncert', self.yErrComboBox)

        self.ecComboBox = ColumnComboBox(self, ColumnTypes.ErrorCorrelation)
        self.ecComboBox.columnChanged.connect(lambda s: view.setProperty('ecColumn', s))
        self.layout().insertRow(5, 'Correlation', self.ecComboBox)        

